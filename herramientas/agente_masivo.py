#!/usr/bin/env python3
"""Agente masivo de datos públicos: de un catálogo completo a fichas de oportunidad validadas.

Uso:
  python herramientas/agente_masivo.py <dominio> --trabajo <carpeta> [--top 8] [--min-filas 1000000]
                                       [--catalogo fuentes/catalogo] [--motor claude|agy|codex|ninguno] [--actualizar] [--validar]
                                       [--solo-validar]

La IA propone y una prueba sin IA comprueba. Los pasos sin IA corren solos; el de IA lo hace el motor que se tenga:
  1. catálogo: explorador_catalogo.py mide todos los conjuntos (reanudable con la caché de --catalogo);
  2. relevancia: relevancia_catalogo.py ordena por si permiten decir estado, lugar e impacto, y por tamaño;
  3. candidatos: los --top mejores con al menos --min-filas y estado, lugar e impacto;
  4. dictamen medido: dictamen_bigdata.py por candidato (<trabajo>/fichas/<id>.dictamen.json): la IA no lo escribe;
  5. encargo: <trabajo>/ENCARGO.md, desde plantillas/encargo_fichas.md, con los candidatos;
  6. IA: con --motor claude, agy o codex se lanza esa CLI sin interacción con el encargo (binarios: CLAUDE_BIN, AGY_BIN y
     CODEX_BIN; Claude usa el perfil de CLAUDE_CONFIG_DIR); con --motor ninguno se imprime el texto para pegarlo en otra IA;
  7. validación sin IA: validar_ficha.py por ficha, SIN caché y contra la fuente real → <trabajo>/RESULTADO.md;
  8. whitepaper para el estudiante, en TRES hojas tamaño carta (<trabajo>/WHITEPAPER.pdf y .html): la IA puede escribir
     el resumen (RESUMEN_IA.md), que entra solo si pasa una comprobación sin IA; el ANÁLISIS lo hace el estudiante.
Después de esto, el juicio de valor lo hacen un juez ciego y las personas: el validador mide la forma, no el valor.

Uso local: el agente se USA, no se modifica. La IA solo escribe en la carpeta de trabajo; aunque haga una investigación,
nunca toca el agente. Para que no dependa de que la IA obedezca:
  - antes de darle el turno, se sella la huella SHA-256 de lo que forma el agente (herramientas/, plantillas/, baterias/,
    flujo.js, orquestar.mjs y los documentos de uso); al terminar se compara: si algo cambió, la corrida NO VALE y se
    nombran los archivos (no se restauran solos: en la misma carpeta pueden trabajar otras personas);
  - la validación del paso 7 corre con las herramientas de la versión de Git (git archive HEAD), no con las de la carpeta;
  - el catálogo, las fichas y los resultados viven en fuentes/, que está fuera de Git: nada de una corrida se publica.
Autoprueba sin red: python herramientas/agente_masivo.py --autoprueba
"""
import hashlib
import json
import os
import shutil
import tempfile
import subprocess
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
PY = sys.executable


def correr(*args, salida=None):
    p = subprocess.run([PY, *map(str, args)], capture_output=True, text=True, cwd=RAIZ)  # nosec B603
    if salida:
        Path(salida).write_text(p.stdout + p.stderr, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


PROTEGIDO = ("herramientas", "plantillas", "baterias", "flujo.js", "orquestar.mjs", "AGENTE-MASIVO.md", "README.md",
             "requirements.txt")


def sellar(raiz=RAIZ, protegido=PROTEGIDO):
    """Huella SHA-256 de cada archivo que forma el agente (sin cachés de Python)."""
    huellas = {}
    for nombre in protegido:
        p = Path(raiz) / nombre
        archivos = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else []
        for f in archivos:
            if "__pycache__" in f.parts or f.suffix == ".pyc":
                continue
            huellas[str(f.relative_to(raiz))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return huellas


def comparar(antes, despues):
    """Archivos del agente que cambiaron, aparecieron o desaparecieron mientras trabajaba la IA."""
    return sorted(k for k in set(antes) | set(despues) if antes.get(k) != despues.get(k))


def herramientas_de_git():
    """Copia de herramientas/ y baterias/ tal como están en HEAD: la validación no usa lo que la IA pudo tocar."""
    destino = Path(tempfile.mkdtemp(prefix="agente-masivo-git-"))
    paq = subprocess.run(["git", "-C", str(RAIZ), "archive", "HEAD", "herramientas", "baterias"],  # nosec B603 B607
                         capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(destino)], input=paq, check=True)  # nosec B603 B607
    return destino / "herramientas"


def autoprueba():
    """Sin red: el sello detecta un cambio, un archivo nuevo y uno borrado, y no da falsas alarmas."""
    d = Path(tempfile.mkdtemp(prefix="agente-masivo-prueba-"))
    (d / "herramientas").mkdir()
    (d / "herramientas" / "validar_ficha.py").write_text("x = 1\n")
    (d / "herramientas" / "otra.py").write_text("y = 2\n")
    casos = []
    antes = sellar(d, ("herramientas",))
    casos.append(("sin cambios no hay alarma", comparar(antes, sellar(d, ("herramientas",))) == []))
    (d / "herramientas" / "validar_ficha.py").write_text("x = 1  # la IA aflojó el validador\n")
    casos.append(("un cambio se detecta", comparar(antes, sellar(d, ("herramientas",))) == ["herramientas/validar_ficha.py"]))
    (d / "herramientas" / "nuevo.py").write_text("z = 3\n")
    (d / "herramientas" / "otra.py").unlink()
    cambiados = comparar(antes, sellar(d, ("herramientas",)))
    casos.append(("lo nuevo y lo borrado se detectan", "herramientas/nuevo.py" in cambiados and "herramientas/otra.py" in cambiados))
    shutil.rmtree(d, ignore_errors=True)
    for nombre, ok in casos:
        print(f"  {'✓' if ok else '✗'} {nombre}")
    errores = sum(not ok for _, ok in casos)
    print("RESUMEN " + json.dumps({"autoprueba": len(casos), "errores": errores}))
    return 1 if errores else 0


def resumen(texto):
    for linea in reversed(texto.splitlines()):
        if linea.startswith("RESUMEN "):
            try:
                return json.loads(linea[8:])
            except ValueError:
                return None
    return None


def main(argv):
    if argv[:1] == ["--autoprueba"]:
        return autoprueba()
    if len(argv) < 3 or "--trabajo" not in argv:
        raise SystemExit(__doc__)
    g = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    dominio, trabajo = argv[0], Path(g("--trabajo")).resolve()
    top, min_filas = int(g("--top", 8)), int(g("--min-filas", 1_000_000))
    catalogo = (RAIZ / g("--catalogo", "fuentes/catalogo")).resolve()
    motor = g("--motor", "ninguno")
    fichas = trabajo / "fichas"
    fichas.mkdir(parents=True, exist_ok=True)
    nombre = dominio.replace("www.", "").replace(".", "_")
    inventario = catalogo / f"inventario_{nombre}.json"

    if "--solo-validar" not in argv:
        print("1-2. catálogo y relevancia (sin IA)…", flush=True)
        if "--actualizar" in argv or not (catalogo / ".cache.json").exists():
            # el conteo de todo el catálogo tarda horas la primera vez; después basta la caché (--actualizar lo retoma)
            correr(AQUI / "explorador_catalogo.py", dominio, "--salida", catalogo, "--hilos", 4, "--min-filas", min_filas)
        rc, out = correr(AQUI / "relevancia_catalogo.py", dominio, "--catalogo", catalogo, "--top", 0)
        rel = json.loads((catalogo / f"relevancia_{nombre}.json").read_text(encoding="utf-8"))
        cand = [r for r in rel if (r.get("filas") or 0) >= min_filas and r["dice_estado"] and r["dice_lugar"] and r["dice_impacto"]][:top]
        if not cand:
            raise SystemExit("No hay candidatos: baje --min-filas o espere a que termine el conteo del catálogo.")
        print(f"3. candidatos: {', '.join(c['id'] for c in cand)}", flush=True)
        for c in cand:
            d = fichas / f"{c['id']}.dictamen.json"
            previos = [RAIZ / "fuentes" / "fichas" / d.name] + sorted((RAIZ / "fuentes" / "fichas").glob(f"*/fichas/{d.name}"))
            previo = next((x for x in previos if x.exists() and x.resolve() != d.resolve()), None)
            if not d.exists() and previo:
                shutil.copy(previo, d)
            if not d.exists():
                print(f"4. dictamen medido de {c['id']}…", flush=True)
                rc, out = correr(AQUI / "dictamen_bigdata.py", "socrata", dominio, c["id"], "--salida", d)
                if not d.exists():
                    print(f"   ✗ no se pudo medir {c['id']} ({out.strip().splitlines()[-1][:120] if out.strip() else 'sin salida'}): "
                          "queda fuera del encargo, sin nivel medido no hay ficha", flush=True)
        cand = [c for c in cand if (fichas / f"{c['id']}.dictamen.json").exists()]
        if not cand:
            raise SystemExit("Ningún candidato tiene dictamen medido: revise la conexión con el portal y repita.")
        lista = "\n".join(f"| {c['id']} | {c['nombre']} | {c['filas']:,} |".replace(",", ".") for c in cand)
        plantilla = (RAIZ / "plantillas" / "encargo_fichas.md").read_text(encoding="utf-8")
        (trabajo / "ENCARGO.md").write_text(
            plantilla.replace("{{DOMINIO}}", dominio).replace("{{CANDIDATOS}}", lista)
            .replace("{{INVENTARIO}}", str(inventario)).replace("{{VALIDADOR}}", str(AQUI / "validar_ficha.py"))
            .replace("{{PYTHON}}", PY), encoding="utf-8")
        print(f"5. encargo: {trabajo / 'ENCARGO.md'}", flush=True)
        pedido = (f"Lee {trabajo / 'ENCARGO.md'} y hazlo completo: una ficha por candidato en {fichas}, cada una validada. "
                  "No modifiques nada fuera de esa carpeta ni los *.dictamen.json. Responde en español con cifras.")
        motores = {   # las mismas invocaciones no interactivas que usa orquestar.mjs; sin servidores MCP del usuario
            "claude": [os.environ.get("CLAUDE_BIN", "claude"), "-p", pedido, "--dangerously-skip-permissions",
                       "--strict-mcp-config", "--add-dir", str(RAIZ)],
            "agy": [os.environ.get("AGY_BIN", "agy"), "--dangerously-skip-permissions", "-p", pedido],
            "codex": [os.environ.get("CODEX_BIN", "codex"), "exec", "--skip-git-repo-check", "--color", "never", "-C", str(trabajo),
                      "--dangerously-bypass-approvals-and-sandbox", pedido],
        }
        if motor in motores and shutil.which(motores[motor][0]):
            sello = sellar()
            (trabajo / "sello_agente.json").write_text(json.dumps(sello, indent=1), encoding="utf-8")
            print(f"6. IA: {motor} escribe las fichas (puede tardar); el agente quedó sellado ({len(sello)} archivos)…", flush=True)
            subprocess.run(motores[motor], cwd=trabajo)  # nosec B603
            tocados = comparar(sello, sellar())
            if tocados:
                aviso = ("✗ LA CORRIDA NO VALE: mientras trabajaba la IA cambiaron archivos del agente (uso local: el agente se usa, "
                         "no se modifica): " + ", ".join(tocados[:20]))
                print(aviso, flush=True)
                (trabajo / "RESULTADO.md").write_text(f"# Corrida inválida\n\n{aviso}\n", encoding="utf-8")
                return 1
            print("   ✓ el agente quedó igual: la IA solo escribió en su carpeta", flush=True)
        else:
            if motor != "ninguno":
                print(f"   (no se encontró la CLI de {motor}: se imprime el texto)", flush=True)
            print("6. IA: pega esto en la IA que uses, con acceso a la carpeta de trabajo:\n\n" + pedido + "\n")
            if "--validar" not in argv:
                return 0

    print("7. validación sin IA, contra la fuente real y sin caché, con las herramientas de la versión de Git…", flush=True)
    try:
        h_git = herramientas_de_git()
    except Exception as e:  # sin Git (por ejemplo, una copia descargada como .zip): se valida con la carpeta y se dice
        print(f"   (sin Git: se valida con las herramientas de la carpeta; {type(e).__name__})", flush=True)
        h_git = AQUI
    filas = []
    for f in sorted(fichas.glob("*.json")):
        if f.name.endswith((".dictamen.json", ".verificacion.json")):
            continue
        rc, out = correr(h_git / "validar_ficha.py", f, "--inventario", inventario, salida=f.with_suffix(".log"))
        r = resumen(out) or {}
        fallas = [l.strip()[2:] for l in out.splitlines() if l.strip().startswith("✗")]
        filas.append((f.stem, r.get("chequeos", "?"), r.get("fallas", "?"), "; ".join(fallas)[:300]))
        print(f"   {f.stem}: {r.get('fallas', '?')} fallas de {r.get('chequeos', '?')}", flush=True)
    md = [f"# Resultado del agente masivo · {dominio} · {datetime.now():%Y-%m-%d %H:%M}", "",
          "La validación sin IA mide la forma (columnas, consultas reales, cruces medidos, gobernanza, sin conclusiones).",
          "Que una ficha pase no la hace publicable: el juicio de valor lo hacen un juez ciego y las personas.", "",
          "| Ficha | Chequeos | Fallas | Qué falló |", "|---|---|---|---|"]
    md += [f"| {a} | {b} | {c} | {d or '—'} |" for a, b, c, d in filas]
    (trabajo / "RESULTADO.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    ok = sum(1 for x in filas if x[2] == 0)
    if filas and motor in ("claude", "agy", "codex") and "--solo-validar" not in argv and not (trabajo / "RESUMEN_IA.md").exists():
        ped = (f"Lee las fichas validadas de {fichas} y su RESULTADO.md, y escribe en {trabajo / 'RESUMEN_IA.md'} un resumen de lo que "
               "se desarrolló para que el estudiante haga el análisis: qué conjuntos se encontraron, por qué son relevantes y qué "
               "preguntas quedan abiertas. Máximo 220 palabras, en español. Sin conclusiones ni recomendaciones (el análisis lo hace el "
               "estudiante), sin cifras salvo años y normas, sin datos personales. No modifiques nada más.")
        cmd = {"claude": [os.environ.get("CLAUDE_BIN", "claude"), "-p", ped, "--dangerously-skip-permissions", "--strict-mcp-config"],
               "agy": [os.environ.get("AGY_BIN", "agy"), "--dangerously-skip-permissions", "-p", ped],
               "codex": [os.environ.get("CODEX_BIN", "codex"), "exec", "--skip-git-repo-check", "--color", "never", "-C", str(trabajo),
                         "--dangerously-bypass-approvals-and-sandbox", ped]}[motor]
        if shutil.which(cmd[0]):
            sello = sellar()
            print(f"8. resumen: {motor} lo escribe (el análisis queda para el estudiante)…", flush=True)
            subprocess.run(cmd, cwd=trabajo)  # nosec B603
            tocados = comparar(sello, sellar())
            if tocados:
                print("✗ LA CORRIDA NO VALE: la IA cambió archivos del agente al escribir el resumen: " + ", ".join(tocados[:20]), flush=True)
                return 1
    if filas:
        print("8. whitepaper de tres hojas carta para el estudiante (resumen de la IA comprobado sin IA)…", flush=True)
        rc_w, out_w = correr(AQUI / "whitepaper_fichas.py", trabajo)
        print("   " + (out_w.strip().splitlines() or ["(sin salida)"])[0], flush=True)
    print(f"RESUMEN {json.dumps({'fichas': len(filas), 'pasan': ok})}")
    return 0 if filas and ok == len(filas) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
