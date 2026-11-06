#!/usr/bin/env python3
"""La compuerta en un solo comando (sin IA, sin llaves, sin red y sin ejecutar nada): ¿este código se puede entregar?

Uso: python herramientas/comprobar.py [--perfil usuario|pura] [--json] archivo.py cuaderno.ipynb carpeta/ ...
     python herramientas/comprobar.py --preparado      (freno de git: revisa lo preparado para el commit, no el disco)

Es lo que conecta la compuerta con cualquier asistente: lo corre un gancho de Claude Code (gancho_compuerta.py), el freno de
git (.githooks/pre-commit), el filtro de GitHub o una persona en una celda de Colab. Mira:
  - la seguridad, con seguridad.py y las reglas por debilidad de seguridad_cwe.py;
  - las librerías: biblioteca estándar y la lista permitida (slopsquatting);
  - en un cuaderno, también las líneas ! y % (instalar paquetes, apagar TLS, claves en un comando).

Código de salida: 0 pasa · 1 no pasa · 2 no se pudo revisar. Si no se pudo revisar, nunca se da por bueno.
"""
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import dependencias  # noqa: E402
import seguridad  # noqa: E402
import seguridad_cwe  # noqa: E402

IGNORAR = {"__pycache__", ".git", ".ipynb_checkpoints", "node_modules"}      # un venv solo se salta si es un entorno de verdad (pyvenv.cfg)
EXTENSIONES = (".py", ".pyw", ".ipynb", ".ipy")
EXCLUIDAS_REPO = ("herramientas/", "baterias/seguridad/malos", "baterias/inyeccion/", "evidencia/", "corridas/", ".githooks/")
INSTALA = re.compile(r"\b(?:pip[\d.]*|python[\d.]*\s+-m\s+pip|uv\s+pip|uv|conda|mamba|poetry)(?:\s+-\S+)*\s+(?:install|add)\b(.*)", re.I)
# una línea ! o %nombre es de IPython; «% x» o «!= x» siguen siendo Python
MAGIA = re.compile(r"^\s*(?:!(?!=)|%%?[A-Za-z_])")
LINEA_PYTHON = re.compile(r"^\s*%(?:time|timeit|prun|memit)\b(?:\s+-\S+(?:\s+\d+)?)*\s*(.*)$")
CELDA_PYTHON = {"time", "timeit", "capture", "prun", "memit", "python", "python3", "pypy"}
ALIAS_PYPI = {"scikit-learn": "sklearn", "beautifulsoup4": "bs4", "pyyaml": "yaml", "python-dotenv": "dotenv", "psycopg2-binary": "psycopg2", "bandit": "bandit"}
CURL_INSEGURO = re.compile(r"\b(?:curl|wget)\b.*\s(?:-k|--insecure|--no-check-certificate)(?:\s|$)")
DESCARGA_EJECUTA = re.compile(r"\b(?:curl|wget)\b[^|;&]*\|\s*(?:sudo\s+)?(?:\w*sh|python[\d.]*|perl|ruby)\b|\b\w*sh\s+<\(\s*(?:curl|wget)|\bpython[\d.]*\s+-c\b|%(?:run|load)\s+(?:\S+\s+)*https?:", re.I)


def es_codigo(ruta):
    return str(ruta).lower().endswith(EXTENSIONES)


def permitidas_usuario():
    return set(json.loads((AQUI / "permitidas_usuario.json").read_text(encoding="utf-8"))["permitidas"])


def librerias(texto, locales=()):
    """Importaciones que no son de la biblioteca estándar ni de la lista permitida."""
    try:
        arbol = ast.parse(texto)
    except SyntaxError:
        return []       # la sintaxis ya la reporta seguridad.py
    mods = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            mods.add(n.module.split(".")[0])
    return sorted(m for m in mods if m not in sys.stdlib_module_names and m not in permitidas_usuario() and m not in locales)


def _paquetes_de(resto):
    """Nombres que instala una línea pip, sin opciones ni versiones. Un archivo de requisitos no se revisa aquí; un paquete remoto sí se marca."""
    resto = re.split(r"[;&|#]", resto)[0]
    return [re.split(r"[=<>!~\[;]", x)[0].lower() for x in resto.split() if not x.startswith(("-", "/", ".", "$", "{")) and ("://" in x or not x.endswith((".txt", ".whl")))]


def _revisa_comando(ln, ubic, ok, hallazgos):
    """Lo que se revisa de una línea ! o % o de una celda de comandos."""
    m = INSTALA.search(ln)
    if m:
        for paquete in _paquetes_de(m.group(1)):
            if ALIAS_PYPI.get(paquete, paquete) not in ok:
                hallazgos.append({"linea": ubic, "regla": f"instala {paquete}", "detalle": "no está en la lista permitida: la IA inventa paquetes. Qué se hace: comprobar en pypi.org y pedirle a la persona responsable que decida"})
    if seguridad_cwe.TLS_TEXTO.search(ln) or CURL_INSEGURO.search(ln):
        hallazgos.append({"linea": ubic, "regla": "CWE-295 · TLS sin verificar", "detalle": "un comando apaga la verificación del certificado. Qué se hace: quitar esa opción"})
    if any(rx.search(ln) for rx, _ in seguridad_cwe.CADENAS_SECRETAS):
        hallazgos.append({"linea": ubic, "regla": "CWE-798 · secreto en el código", "detalle": "un comando lleva una clave escrita. Qué se hace: leerla de una variable de entorno"})
    if DESCARGA_EJECUTA.search(ln):
        hallazgos.append({"linea": ubic, "regla": "CWE-494 · ejecuta código sin revisar", "detalle": "un comando corre código descargado o escrito en la misma línea. Qué se hace: guardar el código en un archivo .py del proyecto"})


def _profundidad(ln, previa):
    """Paréntesis abiertos tras la línea, sin contar cadenas ni comentarios (aproximado)."""
    sin = re.sub(r"\'[^\']*\'|\"[^\"]*\"", "", ln).split("#")[0]
    return max(0, previa + sum(sin.count(c) for c in "([{") - sum(sin.count(c) for c in ")]}"))


def _celda_python(texto, ubic, ok, hallazgos):
    """Devuelve las líneas Python de una celda: su código tal cual si es Python válido; si no, con cada línea de magia revisada aparte."""
    lineas = re.split(r"\r\n|\r|\n", texto)     # IPython también corta en el retorno de carro
    try:
        ast.parse("\n".join(lineas))
        return lineas
    except SyntaxError:
        pass
    salida, i = [], 0
    comandos = False
    while i < len(lineas) and not comandos:     # magias de celda: %%time y %%capture corren su cuerpo como Python, y se pueden apilar
        s = lineas[i].strip()
        m = re.match(r"%%\s*(\S*)\s*(.*)", s)
        if s and not m:
            break
        if m:
            nombre, resto = m.group(1).lower(), m.group(2)
            _revisa_comando(s, ubic, ok, hallazgos)
            comandos = not (nombre in CELDA_PYTHON or (nombre in ("writefile", "file") and resto.lower().endswith(".py")))
        salida.append("")
        i += 1
    prof, sigue = 0, False
    for ln in lineas[i:]:
        if comandos:
            _revisa_comando(ln, ubic, ok, hallazgos)
            salida.append("")
            continue
        sangria = ln[:len(ln) - len(ln.lstrip())]
        es_magia = not prof and not sigue and MAGIA.match(ln)
        if es_magia:
            _revisa_comando(ln, ubic, ok, hallazgos)
            m = LINEA_PYTHON.match(ln)
            ln = sangria + m.group(1) if m and m.group(1) else sangria + "pass  # (línea de cuaderno, revisada aparte)"
        salida.append(ln)
        prof, sigue = _profundidad(ln, prof), ln.rstrip().endswith("\\")
    return salida


def _textos_fuera_del_codigo(d):
    """Cadenas de salidas, metadatos y markdown del cuaderno, sin el código de las celdas ni las imágenes."""
    pila = [d]
    while pila:
        x = pila.pop()
        if isinstance(x, str):
            yield x
        elif isinstance(x, list):
            pila.extend(x)
        elif isinstance(x, dict):
            codigo = x.get("cell_type") == "code"
            pila.extend(v for k, v in x.items() if not (codigo and k in ("source", "input")) and not str(k).startswith("image/") and k != "application/pdf")


def _celdas_de(d):
    """Celdas de código en nbformat 4 y 3 (worksheets). Un cuaderno con forma rara no se puede revisar."""
    if not isinstance(d, dict):
        raise ValueError("el cuaderno no tiene la forma esperada")
    grupos = [d.get("cells", [])] + [w.get("cells", []) if isinstance(w, dict) else None for w in d.get("worksheets", []) or []]
    if not any(k in d for k in ("cells", "worksheets")):
        raise ValueError("el cuaderno no tiene celdas")
    salida = []
    for grupo in grupos:
        if not isinstance(grupo, list):
            raise ValueError("el cuaderno no tiene la forma esperada")
        for c in grupo:
            if not isinstance(c, dict):
                raise ValueError("el cuaderno no tiene la forma esperada")
            if c.get("cell_type") == "code":
                fuente = c.get("source", c.get("input", []))
                if isinstance(fuente, list) and all(isinstance(x, str) for x in fuente):
                    salida.append("".join(fuente))
                elif isinstance(fuente, str):
                    salida.append(fuente)
                else:
                    raise ValueError("una celda del cuaderno no tiene la forma esperada")
    return salida


def de_cuaderno(ruta):
    """Devuelve (código, celda por línea, hallazgos de las líneas ! y %) de un cuaderno o un .ipy. Lo que corre como Python se revisa como Python; las magias, aparte."""
    bruto = seguridad.leer_bytes(ruta).decode("utf-8-sig")
    ipy = str(ruta).lower().endswith(".ipy")
    d = None if ipy else json.loads(bruto)
    lineas, celdas, hallazgos = [], [], []
    # lo que se instala en un cuaderno es lo que se importa: PyPI nombra distinto algunos (scikit-learn, beautifulsoup4, PyYAML)
    ok = {p.lower() for p in permitidas_usuario()} | {"bandit"}
    for numero, texto in enumerate([bruto] if ipy else _celdas_de(d), 1):
        for ln in _celda_python(texto, f"celda {numero}", ok, hallazgos):
            lineas.append(ln)
            celdas.append(numero)
    if not ipy and any(any(rx.search(t) for rx, _ in seguridad_cwe.CADENAS_SECRETAS) for t in _textos_fuera_del_codigo(d)):
        hallazgos.append({"linea": "salidas o metadatos", "regla": "CWE-798 · secreto en el cuaderno", "detalle": "una salida, un metadato o un texto lleva una clave. Qué se hace: limpiar las salidas, cambiar esa clave y leerla de una variable de entorno"})
    return "\n".join(lineas) + "\n", celdas, hallazgos


def recoger(rutas):
    out, faltan = [], []
    for texto in rutas:
        r = Path(texto)
        if not str(texto):
            faltan.append("(ruta vacía)")
        elif r.is_dir():
            for carpeta, subs, archivos in os.walk(r, onerror=lambda e: faltan.append(str(e.filename))):
                base = Path(carpeta)
                for s in list(subs):
                    if s in IGNORAR or (base / s / "pyvenv.cfg").exists():
                        subs.remove(s)
                    elif (base / s).is_symlink():
                        faltan.append(str(base / s))
                subs.sort()
                out += [base / a for a in sorted(archivos) if es_codigo(a) and (base / a).is_file()]
        elif r.is_file() and es_codigo(r):
            out.append(r)
        else:
            faltan.append(str(r))
    return out, faltan


def revisar_archivos(rutas, perfil="usuario", locales_por_archivo=None):
    """Una entrada por archivo: {"archivo", "pasa", "hallazgos": [{linea, regla, detalle}]}. Lanza OSError o ValueError si no se puede leer."""
    salida = []
    with tempfile.TemporaryDirectory(prefix="compuerta-") as tmp:
        planes = []
        for i, r in enumerate(rutas):
            r = Path(r)
            if r.suffix.lower() in (".ipynb", ".ipy"):
                texto, celdas, magia = seguridad.con_tope(seguridad.TOPE_SEG_ARCHIVO, de_cuaderno, r)
                copia = Path(tmp) / f"c{i}.py"
                copia.write_text(texto, encoding="utf-8")
                planes.append((r, copia, celdas, magia, texto))
            else:
                planes.append((r, r, None, [], seguridad.leer_fuente(r)))
        res, aviso = seguridad.revisar([p[1] for p in planes], perfil) if planes else ([], None)
        if aviso:
            raise ValueError(aviso)
        for (r, _copia, celdas, magia, texto), rv in zip(planes, res):
            hall = list(magia)
            for h in rv["bloquean"]:
                h = dict(h)
                n = h.get("linea")
                if celdas and isinstance(n, int) and 0 < n <= len(celdas):
                    h["linea"] = f"celda {celdas[n - 1]}"
                hall.append(h)
            if perfil == "usuario":
                locales = (locales_por_archivo or {}).get(str(r)) or {p.stem for p in r.resolve().parent.glob("*.py")}
                for m in librerias(texto, locales):
                    hall.append({"linea": "importación", "regla": f"librería fuera de la lista: {m}", "detalle": "la IA inventa paquetes y un atacante los puede registrar. Qué se hace: comprobar en pypi.org si existe y pedirle a la persona responsable que decida si entra a la lista"})
            else:
                d = dependencias.revisar(r if r.suffix == ".py" else _copia)
                for m in d.get("no_permitidas") or []:
                    hall.append({"linea": "importación", "regla": f"librería fuera de la lista: {m}", "detalle": "solo biblioteca estándar y permitidas.json"})
                for m in d.get("intenta_instalar") or []:
                    hall.append({"linea": "código", "regla": "intenta instalar", "detalle": m})
            salida.append({"archivo": str(r), "pasa": not hall, "hallazgos": hall})
    return salida


def _informe(res, faltan, perfil, como_json, nombres=None):
    nombres = nombres or {}
    res = [{**r, "archivo": nombres.get(r["archivo"], r["archivo"])} for r in res]
    resumen = {"perfil": perfil, "archivos": len(res), "no_pasan": sum(not r["pasa"] for r in res), "no_encontrados": len(faltan)}
    if como_json:
        print(json.dumps({"resumen": resumen, "archivos": res, "no_encontrados": faltan}, ensure_ascii=False, indent=1))
    else:
        for r in res:
            print(f"{'✓ PASA' if r['pasa'] else '✗ NO PASA'} · {r['archivo']}")
            for h in r["hallazgos"]:
                print(f"    {h['linea']}: {h['regla']} ({h['detalle']})")
        for f in faltan:
            print(f"? no encontrado, ilegible o no es código Python: {f}")
        print("RESUMEN " + json.dumps(resumen, ensure_ascii=False))
    return resumen


def _git(raiz, *a):
    p = subprocess.run(["git", "-c", "core.quotepath=off", *a], cwd=raiz, capture_output=True, timeout=60)  # nosec B603 B607
    if p.returncode != 0:
        raise ValueError(f"git falló ({a[0]})")
    return p.stdout


def revisar_preparado(perfil="usuario"):
    """Freno de git: revisa lo que va a entrar al commit (el índice), no lo que hay en el disco."""
    raiz = Path(os.fsdecode(_git(".", "rev-parse", "--show-toplevel")).strip())
    campos = [os.fsdecode(x) for x in _git(raiz, "diff", "--cached", "--name-status", "-z", "--diff-filter=ACMRT").split(b"\0") if x]
    preparados, i = [], 0
    while i < len(campos):
        pasos = 2 if campos[i][0] in "RC" else 1      # renombrado o copia: estado, origen, destino
        preparados.append(campos[i + pasos])
        i += pasos + 1
    propio = AQUI == raiz / "herramientas"       # las carpetas excluidas solo valen en este mismo repositorio
    bloqueados = [r for r in preparados if r.lower().endswith(".bloqueado")]
    elegidos = [r for r in preparados if es_codigo(r) and not (propio and r.startswith(EXCLUIDAS_REPO))]
    for r in bloqueados:
        print(f"✗ NO PASA · {r}\n    archivo: cuarentena (la compuerta lo apartó. Qué se hace: lo decide una persona; no se sube)")
    if not elegidos:
        return 1 if bloqueados else 0
    conocidos = [os.fsdecode(x) for x in _git(raiz, "ls-files", "--cached", "-z").split(b"\0") if x]
    with tempfile.TemporaryDirectory(prefix="compuerta-freno-") as tmp:
        nombres, locales, copias = {}, {}, []
        for i, r in enumerate(elegidos):
            copia = Path(tmp).resolve() / f"f{i}{Path(r).suffix.lower()}"
            copia.write_bytes(_git(raiz, "cat-file", "blob", f":0:{r}"))
            copias.append(copia)
            nombres[str(copia)] = r
            locales[str(copia)] = {Path(x).stem for x in conocidos if Path(x).parent == Path(r).parent and x.lower().endswith(".py")}
        res = revisar_archivos(copias, perfil, locales)
        resumen = _informe(res, [], perfil, False, nombres)
    return 1 if resumen["no_pasan"] or bloqueados else 0


def _main(argv):
    perfil = "usuario"
    if "--perfil" in argv:
        i = argv.index("--perfil")
        if i + 1 >= len(argv):
            print("NO SE PUDO REVISAR: --perfil necesita un valor (usuario o pura).", file=sys.stderr)
            return 2
        perfil = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    como_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if "--preparado" in argv:
        return revisar_preparado(perfil)
    if not argv:
        raise SystemExit(__doc__)
    rutas, faltan = recoger(argv)
    res = revisar_archivos(rutas, perfil)
    resumen = _informe(res, faltan, perfil, como_json)
    if faltan or not res:
        return 2
    return 1 if resumen["no_pasan"] else 0


def main(argv):
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(errors="backslashreplace")     # un carácter raro en el informe no puede tumbar la revisión
    try:
        return _main(argv)
    except Exception as e:  # falla cerrada: toda caída es «no se pudo revisar», nunca una aprobación
        print(f"NO SE PUDO REVISAR ({type(e).__name__}): {e}. Qué se hace: revisar que Bandit esté instalado (pip install --require-hashes -r requirements-compuerta.txt) y que el archivo sea legible; sin revisión no se da por bueno.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
