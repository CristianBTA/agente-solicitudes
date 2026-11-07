#!/usr/bin/env python3
"""Filtro automático de aportes (sin IA y sin llaves: no le gasta nada a nadie).

Uso:
  python herramientas/validar_aporte.py [--base upstream/main] [--arbol <carpeta del aporte>]
  python herramientas/validar_aporte.py --autoprueba [--solo caso1,caso2]
      prueba al filtro: en clones temporales del último commit arma aportes dañados a propósito; el juez debe
      rechazarlos todos y dejar pasar el clon intacto

El juez no sale del aporte. En GitHub Actions corre el validar_aporte.py de la BASE contra el árbol del aporte
(--arbol), y las herramientas con que prueba también salen de la base: arma una copia temporal con los archivos del
aporte y, encima, las herramientas, el flujo, las dependencias y la configuración de GitHub de la base. Un aporte que
cambia algo de eso no pasa solo: queda como falla «requiere decisión del dueño», nunca como ✓.

Revisa:
  1. Archivos que no pueden entrar: datos, por su contenido y no por su extensión (una tabla .tsv, .txt o JSONL fuera
     de ejemplo/datos, baterias y caso_conocido; un CSV de más de 200 KB; cualquier archivo de más de 1 MB; un caso
     conocido de más de 200 filas; un JSON con más de 1.000 objetos; 100 o más ids de SECOP II en un archivo),
     carpetas datos/ o limpio/, entornos, cachés, llaves, la configuración de asistentes y editores que se ejecuta o
     se obedece sola al abrir el clon (L54) y enlaces simbólicos. Los flujos, las plantillas y CODEOWNERS de .github/
     y los ganchos de .githooks/ solo los cambia el dueño: de otra persona son falla, y del dueño, «requiere decisión
     del dueño». Las rutas se comparan como las ve el disco de macOS (el runner y el Mac del dueño): sin mayúsculas, con
     los acentos en una sola forma y sin los invisibles que ignora HFS+. Una ruta que ahí cae sobre otra escrita distinto
     («.Githooks/pre-commit», «Flujo.js», «agentes/00-Reglas-comunes.md») es falla y su contenido no se revisa: git deja
     un solo archivo en el disco, y el juez leería el de la base mientras el clon del dueño recibe el del aporte (L99).
  2. Datos personales en todo lo que el aporte agrega (barrido de gobernanza) y, en toda tabla, que las columnas que
     identifican a personas solo traigan valores con la forma ficticia de la guía; en baterias/privacidad/, también
     lo que encuentre el barrido.
  3. Seguridad de todo código Python agregado o cambiado (compuertas: librerías permitidas, reglas propias y
     Bandit; los cuadernos .ipynb, con el comando de la compuerta). La excepción son las muestras de
     baterias/seguridad/malos/ y malos_usuario/, que justamente deben bloquearse.
  4. Que no rompa nada: baterías, la corrida sintética verificada desde cero y las 13 mutantes atrapadas. Una
     herramienta que se cae antes de su línea RESUMEN no aprueba nada: es falla, aunque no haya escrito ninguna «✗» (L67).
  5. Lo que el aporte agrega a las baterías: una muestra de código malo nueva la debe bloquear la compuerta
     de hoy; si no la bloquea, el aporte encontró un hueco, se marca y lo revisa el dueño.
  6. El SGSI (sgsi/README.md): nada restringido versionado, sin llaves, flujos de solo lectura y cada control con evidencia.
  7. Si el aporte cambia una herramienta: el banco de blindaje de la base contra las herramientas del aporte, y las
     baterías con las herramientas del aporte. Lo que ceda o falle es falla; que pase no basta: lo decide el dueño.
Sale con 0 si pasa, con 1 si no pasa y con 2 si no pudo revisar (la carpeta no es la raíz de un repositorio git o la
base no existe): nunca cambia de base ni revisa otra cosa en silencio. FAILFAST también para el filtro: si una de sus
herramientas no termina, sale con un código distinto de 0 o no deja su línea RESUMEN, el aporte no pasa.
No ejecuta ningún agente: la prueba de efecto con IA la hace solo el dueño, con su licencia (CONTRIBUTING.md).
"""
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

JUEZ = Path(__file__).resolve()
RAIZ = JUEZ.parent.parent
sys.path.insert(0, str(RAIZ / "herramientas"))
from gobernanza import (parece_instruccion, INSTRUCCION, COMENTARIO_OCULTO, PATRONES,  # noqa: E402
                        clasificar_columna, es_sensible)
from rutas_protegidas import clave, colisiones  # noqa: E402  (una sola forma de comparar rutas, L99)


def ordenes_a_agentes(texto):
    """Un aporte no puede traer texto que dé órdenes a los agentes (inyección por el canal de aportes)."""
    return parece_instruccion(texto)


def cuenta_ordenes(texto):
    """Cuántas frases con forma de orden trae un texto (para saber si un cambio agrega una nueva)."""
    return sum(1 for _ in INSTRUCCION.finditer(texto)) + sum(1 for c in COMENTARIO_OCULTO.findall(texto) if parece_instruccion(f"<!--{c}-->"))
import comprobar  # noqa: E402
import dependencias  # noqa: E402
import seguridad  # noqa: E402

PROHIBIDOS = re.compile(r"(^|/)(\.venv|venv|__pycache__|\.env|node_modules)(/|$)|(^|/)(datos|limpio)/.*\.csv$"
                        r"|\.(pem|key|p12|pfx|sqlite|db|parquet|xlsx?|zip|gz|bloqueado)$|(^|/)ejemplo-secop/datos/"
                        r"|(^|/)(\.env[^/]*|\.npmrc|\.pypirc|\.netrc|id_(rsa|dsa|ecdsa|ed25519)(\.pub)?)$", re.I)
# Configuración de asistentes y editores: se ejecuta o se obedece sola cuando el dueño abre el clon (servidores MCP,
# ganchos, tareas que corren al abrir la carpeta, contenedores con comandos de arranque, instrucciones que el asistente
# carga sin que nadie las lea). Un aporte de datos o de reglas nunca la necesita (L54).
ASISTENTES = re.compile(r"(^|/)(\.claude|\.cursor|\.vscode|\.idea|\.devcontainer|\.gemini|\.codex|\.continue|\.windsurf"
                        r"|\.roo|\.kiro|\.amazonq|\.agents?)(/|$)"
                        r"|(^|/)(\.mcp\.json|CLAUDE(\.local)?\.md|GEMINI\.md|\.cursorrules|\.windsurfrules|\.clinerules"
                        r"|\.aider[^/]*|\.pre-commit-config\.ya?ml|\.gitmodules|\.envrc)$", re.I)
# Solo los cambia el dueño: los flujos de GitHub corren en sus máquinas al aprobar la corrida de un fork, y CODEOWNERS
# decide quién revisa (L54). En GitHub el juez sale de la base (L68), pero en el clon de quien aporta corre su propia
# copia: si el aporte toca el filtro o lo que importa, ese verde no prueba nada y el dueño lo revisa línea por línea.
DEL_DUENO = re.compile(r"^\.git(hub|hooks)/")   # .githooks corre sola en cada commit de quien activó el freno
CADENA_DEL_FILTRO = re.compile(r"^(herramientas/(validar_aporte|rutas_protegidas|gobernanza|rutas|seguridad|seguridad_cwe|comprobar|gancho_compuerta|dependencias|blindaje|sgsi|caja|integridad)\.py"
                               r"|herramientas/permitidas(_usuario)?\.json|requirements(-compuerta)?\.txt)$")
MUESTRAS_MALAS = ("baterias/seguridad/malos/", "baterias/seguridad/malos_usuario/")
CSV_PERMITIDOS = re.compile(r"^(ejemplo/datos/|baterias/|corridas/[^/]+/caso_conocido/)")
MAX_CSV = 200_000
# Datos por su contenido, no por su extensión (un .tsv, un .json o un .txt también pueden traer el extracto)
MAX_BYTES = 1_000_000            # cualquier archivo; hoy el más grande, fuera del gráfico, pesa 124 KB
MAX_BYTES_GRAFICO = 6_000_000    # corridas/*/grafico.html trae el paquete de Plotly (4,8 MB); sin él, rige MAX_BYTES
MAX_FILAS_CASO = 200             # un caso conocido es pequeño: el flujo pide de 8 a 25 filas (hoy, 23 como mucho)
MAX_FILAS_EJEMPLO = 5_000        # ejemplo/datos (sintético): ventas.csv tiene 1.520
MAX_OBJETOS_JSON = 1_000         # listas de objetos en JSON de configuración o de informes (hoy, 95 como mucho)
MAX_IDS_SECOP = 100              # ids de SECOP II en un archivo (hoy, 23 como mucho, en un caso conocido sintético)
ID_SECOP = re.compile(r"\bCO1\.(?:PCCNTR|BDOS|PPI|REQ|NTFCC)\.\d{4,}\b")
BINARIOS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf")
NO_TABULARES = (".py", ".js", ".mjs", ".md", ".html", ".htm", ".yml", ".yaml", ".svg") + BINARIOS
FICTICIO = re.compile(r"ficticia|ficticio|inventad", re.I)
CORRIDA_REFERENCIA = "corridas/2026-11-06-ventas-semestre"
MUTANTES = "evidencia/sintetico/mutantes"
# Lo que juzga a los aportes. Si un aporte lo cambia, no se juzga con su propia versión: lo decide el dueño.
CONFIABLES = ("herramientas/", ".github/", ".githooks/", "flujo.js", "requirements.txt", "requirements-compuerta.txt")
ESTADOS = {"A": "agrega", "M": "cambia", "D": "borra", "T": "cambia el tipo de"}
# Por qué el dueño decide cada grupo de «requiere decisión del dueño» (lo que no está aquí es parte del juez)
MOTIVO_DUENO = {"rutas que chocan": "en macOS y Windows reemplazan a otra ruta escrita distinto (L99)"}


def motivo_prohibido(ruta):
    """Por qué una ruta no puede entrar en un aporte (None si puede). Se mira la clave de la ruta (L99)."""
    if ASISTENTES.search(clave(ruta)):
        return f"configuración de asistente o editor que se ejecuta o se obedece al abrir el clon: {ruta}"
    if PROHIBIDOS.search(clave(ruta)):
        return f"archivo que no puede entrar: {ruta}"
    return None


def solo_del_dueno(ruta):
    """Los flujos, plantillas y CODEOWNERS de .github/ y los ganchos de .githooks/, con cualquier grafía: en macOS,
    «.Githooks/pre-commit» es el gancho que corre en cada commit del dueño (L99)."""
    return DEL_DUENO.match(clave(ruta)) is not None


def es_del_dueno():
    """El pull request lo abrió el dueño (GitHub lo dice en el evento; a mano se asume que no)."""
    evento = os.environ.get("GITHUB_EVENT_PATH")
    try:
        return json.loads(Path(evento).read_text(encoding="utf-8"))["pull_request"]["author_association"] == "OWNER"
    except Exception:
        return False


class SinRevisar(Exception):
    """El filtro no pudo revisar el aporte: sale con 2 y dice por qué."""


def git(d, *a, binario=False):
    try:
        p = subprocess.run(["git", "-c", "core.quotepath=off", *a], cwd=d, capture_output=True, check=True)  # nosec B603 B607
    except FileNotFoundError:
        raise SinRevisar("no hay git en esta máquina") from None
    except subprocess.CalledProcessError as e:
        raise SinRevisar(f"«git {' '.join(a)[:90]}» falló en {d}: "
                         f"{e.stderr.decode('utf-8', 'replace').strip()[:240] or 'sin mensaje'}") from None
    return p.stdout if binario else p.stdout.decode("utf-8", "replace")


def existe_en_git(d, *a):
    try:
        return subprocess.run(["git", "-c", "core.quotepath=off", *a], cwd=d, capture_output=True).returncode == 0  # nosec B603 B607
    except FileNotFoundError:
        raise SinRevisar("no hay git en esta máquina") from None


def mostrar(d, sha, ruta):
    """Contenido de un archivo en un commit, o "" si no existe ahí."""
    if not existe_en_git(d, "cat-file", "-e", f"{sha}:{ruta}"):
        return ""
    return git(d, "show", f"{sha}:{ruta}")


def resumen(texto):
    """La línea RESUMEN de una herramienta como diccionario; None si falta o no es JSON."""
    for linea in reversed(texto.splitlines()):
        if linea.startswith("RESUMEN "):
            try:
                d = json.loads(linea[len("RESUMEN "):])
            except ValueError:
                return None
            return d if isinstance(d, dict) else None
    return None


def ultima(texto):
    return (texto.strip().splitlines() or ["(sin salida)"])[-1][:200]


def correr(raiz, *a, entorno=None):
    p = subprocess.run([sys.executable, *a], cwd=raiz, capture_output=True, text=True, env=entorno)  # nosec B603
    return p.returncode, p.stdout + p.stderr, resumen(p.stdout)


_LEER = object()


def revisar_baterias(rc, out, nuevos_bateria, res=_LEER):
    """Fallas y avisos de baterias.py, desde su RESUMEN: cada falla trae su caso, y la que causa un caso NUEVO del aporte
    es un hueco encontrado (aviso, valioso). Unas baterías que se caen antes de su RESUMEN (por ejemplo, por un JSON
    roto) no escriben ninguna «✗» y no prueban nada: es falla, venga de donde venga el archivo (L67). Una salida con
    error, o con «✗», sin decir qué falló también es falla. `res` es el RESUMEN leído de la salida estándar (sin él, se
    lee de `out`)."""
    fallas, avisos = [], []
    if res is _LEER:
        res = resumen(out)
    marcadas = [l for l in out.splitlines() if l.startswith("✗")]
    if res is None:
        fallas.append(f"las baterías no terminaron o no dejaron su RESUMEN (código {rc}): {ultima(out)}")
        fallas += [f"baterías: {l[2:]}"[:300] for l in marcadas]
        return fallas, avisos
    detalle = [x for x in (res.get("detalle") or []) if isinstance(x, dict)]
    for x in detalle:
        if str(x.get("caso", "")).strip() in nuevos_bateria:
            avisos.append(f"hueco encontrado por el aporte (valioso; el dueño decide cómo cerrarlo): {x.get('bateria')}: {x.get('falla')}"[:300])
        else:
            fallas.append(f"baterías: {x.get('bateria')}: {x.get('falla')}"[:300])
    if (rc != 0 or marcadas) and not detalle:
        fallas.append(f"las baterías salieron con código {rc} sin decir qué falló: {ultima(out)}")
    sin_detalle = (res.get("fallas") if isinstance(res.get("fallas"), int) else 0) - len(detalle)
    if sin_detalle > 0:   # el RESUMEN recorta el detalle: lo que no se ve no se puede dar por hueco del aporte
        fallas.append(f"baterías: {sin_detalle} falla(s) más sin detalle en el RESUMEN")
    return fallas, avisos


def revisar_sgsi(rc, out, res=_LEER):
    """Fallas de sgsi.py: cada «✗» de un chequeo, y un SGSI que se cae antes de su RESUMEN o que sale con error sin
    decir por qué (L67)."""
    if res is _LEER:
        res = resumen(out)
    marcadas = [l.strip()[2:] for l in out.splitlines() if l.startswith("    ✗ ")]
    fallas = [f"SGSI: {l[:200]}" for l in marcadas]
    if res is None:
        fallas.append(f"el SGSI no terminó o no dejó su RESUMEN (código {rc}): {ultima(out)}")
    elif rc != 0 and not marcadas:
        fallas.append(f"el SGSI salió con código {rc} sin decir qué falló: {ultima(out)}")
    return fallas


def instrucciones(texto):
    """Los fragmentos con forma de orden a una IA: frases de INSTRUCCION y comentarios ocultos que le hablan a un agente."""
    t = str(texto or "")
    out = {m.group(0).lower() for m in INSTRUCCION.finditer(t)}
    out |= {c.strip().lower()[:200] for c in COMENTARIO_OCULTO.findall(t) if parece_instruccion(f"<!--{c}-->")}
    return out


def confiable_de(ruta):
    """La entrada de CONFIABLES que cubre la ruta, con cualquier grafía (L99), o None."""
    k = clave(ruta)
    return next((c for c in CONFIABLES if k == c.rstrip("/") or k.startswith(c)), None)


def es_confiable(ruta):
    return confiable_de(ruta) is not None


def rutas_en(arbol, sha):
    """Todas las rutas versionadas de un commit."""
    return {r for r in git(arbol, "ls-tree", "-r", "--name-only", "-z", sha).split("\0") if r}


def cambios(arbol, punto):
    """Lo que el aporte cambia desde su punto de partida: commits, cambios sin commit y archivos nuevos sin agregar.
    Sin detectar renombres: renombrar es borrar uno y agregar otro, y así se revisa."""
    vistos = {}
    partes = git(arbol, "diff", "--name-status", "-z", "--no-renames", punto).split("\0")
    for i in range(0, len(partes) - 1, 2):
        vistos[partes[i + 1]] = partes[i][:1]
    for r in git(arbol, "ls-files", "-z", "--others", "--exclude-standard").split("\0"):
        if r:
            vistos.setdefault(r, "A")
    return sorted((e, r) for r, e in vistos.items())


def versionables(arbol):
    return sorted({r for r in git(arbol, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0") if r})


def casos_nuevos(arbol, punto, archivos):
    """Nombres de archivo y líneas que el aporte agrega a las baterías: una falla en uno de ellos es un hueco que
    encontró el aporte (valioso), no un error."""
    nuevos = set()
    for estado, ruta in archivos:
        if not ruta.startswith("baterias/"):
            continue
        if estado == "A":
            nuevos.add(Path(ruta).name)
        elif estado == "M":
            for linea in git(arbol, "diff", "-U0", "--no-color", punto, "--", ruta).splitlines():
                if linea.startswith("+") and not linea.startswith("+++"):
                    t = linea[1:].strip()
                    nuevos.add(t)
                    nuevos.update(re.findall(r'"((?:[^"\\]|\\.)+)"', t))
    return {n for n in nuevos if n}


# ---------------- datos por su contenido: tablas, extractos de SECOP y valores ficticios

def lista_de_objetos(x):
    """La lista de objetos (diccionarios) más larga dentro de un JSON, o None."""
    mejor = None
    pila = [x]
    while pila:
        y = pila.pop()
        if isinstance(y, list):
            if len(y) >= 2 and all(isinstance(e, dict) for e in y) and (mejor is None or len(y) > len(mejor)):
                mejor = y
            pila += [e for e in y if isinstance(e, (list, dict))]
        elif isinstance(y, dict):
            pila += [v for v in y.values() if isinstance(v, (list, dict))]
    return mejor


def tabla_por_contenido(p, texto):
    """(tipo, columnas, filas) si el archivo es una tabla por lo que trae, sin importar la extensión: texto delimitado
    con un número de campos constante (coma, punto y coma, tabulador o «|»), JSON con una lista de objetos o JSONL.
    None si no lo es."""
    s = p.suffix.lower()
    if s in NO_TABULARES:
        return None
    if s in (".json", ".jsonl", ".ndjson") or texto.lstrip()[:1] in ("[", "{"):
        try:
            lista = lista_de_objetos(json.loads(texto))
            tipo = "json"
        except ValueError:
            lista, tipo = [], "jsonl"
            for linea in texto.splitlines():
                if not linea.strip():
                    continue
                try:
                    o = json.loads(linea)
                except ValueError:
                    return None
                if not isinstance(o, dict):
                    return None
                lista.append(o)
        if not lista or len(lista) < 2:
            return None
        cols = sorted({str(k) for o in lista for k in o})
        return tipo, cols, [[str(o.get(c, "")) for c in cols] for o in lista]
    muestra = "\n".join(texto.splitlines()[:200])
    try:
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t|")
        filas = [f for f in csv.reader(io.StringIO(texto), dialecto) if f]
    except csv.Error:
        return None
    if len(filas) < 3 or len(filas[0]) < 2:
        return None
    if sum(1 for f in filas[1:] if len(f) == len(filas[0])) < 0.8 * (len(filas) - 1):
        return None
    return "delimitado", filas[0], filas[1:]


def es_ficticio(valor):
    """La forma ficticia que pide APORTAR-CON-TU-AGENTE.md: «Persona Ficticia Uno», 000.000.001, un correo en
    ejemplo.invalid (o en otro dominio reservado), 399 000 000x. En un texto con letras, también un número de
    relleno con cero adelante («Distribuidora 010 S.A.S.», «FV-001022»): ningún nombre de persona trae cifras. Un valor
    solo de cifras debe tener la forma de la guía (ceros y hasta tres cifras al final): una cuenta real puede empezar por 0."""
    t = str(valor).strip()
    if not t or FICTICIO.search(t):
        return True
    m = re.fullmatch(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)", t)
    if m:
        d = m.group(1).lower()
        return d.endswith((".invalid", ".test", ".example")) or d in ("example.com", "example.org", "example.net")
    digitos = re.sub(r"[\s.\-+()]", "", t)
    if digitos.isdigit():
        return bool(re.fullmatch(r"0+\d{1,3}|(57)?3990000\d{3}", digitos))
    return any(re.fullmatch(r"0\d+", x) for x in re.findall(r"\d+", t))


def ficticio_en_texto(patron, m):
    if patron == "cédula con contexto":
        return bool(re.fullmatch(r"0+\d{1,3}", re.sub(r"\D", "", m.group(1))))
    if patron == "celular":
        return bool(re.fullmatch(r"(57)?3990000\d{3}", re.sub(r"\D", "", m.group(0))))
    if patron == "correo":
        return es_ficticio(m.group(0))
    return bool(FICTICIO.search(m.group(0)))


def revisar_datos(ruta, p):
    """Lo que no puede entrar por su contenido. Devuelve las fallas (una lista de textos)."""
    fallas = []
    tam = p.stat().st_size
    es_grafico = re.fullmatch(r"corridas/[^/]+/grafico\.html", ruta) is not None
    if tam > (MAX_BYTES_GRAFICO if es_grafico else MAX_BYTES):
        fallas.append(f"archivo de {tam:,} bytes (el tope es {MAX_BYTES_GRAFICO if es_grafico else MAX_BYTES:,}; los datos no se publican): {ruta}".replace(",", "."))
    if p.suffix.lower() in BINARIOS:
        return fallas
    texto = p.read_text(encoding="utf-8", errors="ignore")
    if es_grafico:
        sin_plotly = re.sub(r"<script[^>]*>.*?</script>", " ", texto, flags=re.S)
        if len(sin_plotly.encode("utf-8")) > MAX_BYTES:
            fallas.append(f"grafico.html con más de {MAX_BYTES:,} bytes fuera de sus scripts: {ruta}".replace(",", "."))
    ids = set(ID_SECOP.findall(texto))
    if len(ids) >= MAX_IDS_SECOP:
        fallas.append(f"parece un extracto de SECOP II: {len(ids):,} ids de contrato o de proceso distintos (los datos de SECOP no se publican): {ruta}".replace(",", "."))
    tabla = tabla_por_contenido(p, texto)
    privacidad = ruta.startswith("baterias/privacidad/")
    if tabla:
        tipo, cols, filas = tabla
        en_caso = re.match(r"corridas/[^/]+/caso_conocido/", ruta) is not None
        if tipo != "json" and not CSV_PERMITIDOS.match(ruta) and p.suffix.lower() != ".csv":   # el CSV ya tiene su regla
            fallas.append(f"tabla ({tipo}, {len(filas):,} filas) fuera de las carpetas permitidas (ejemplo/datos, baterias, caso_conocido): {ruta}".replace(",", "."))
        if en_caso:
            tope = MAX_FILAS_CASO
        elif ruta.startswith("ejemplo/datos/"):
            tope = MAX_FILAS_EJEMPLO
        elif ruta.startswith("baterias/"):
            tope = None
        else:
            tope = MAX_OBJETOS_JSON if tipo == "json" else None   # una tabla delimitada aquí ya es falla
        if tope is not None and len(filas) > tope:
            fallas.append(f"tabla de {len(filas):,} filas (el tope aquí es {tope:,}; los datos no se publican): {ruta}".replace(",", "."))
        # el encabezado de toda tabla, también en baterias/privacidad/: una columna que identifica a personas o es un dato
        # sensible solo puede traer valores evidentemente ficticios
        personales = [c for c in cols if clasificar_columna(c) == "personal" or es_sensible(c)]
        if tipo == "json" and all(re.fullmatch(r"nombres?", c) for c in personales):
            personales = []   # en un JSON de configuración (sgsi/controles.json), «nombre» solo es la etiqueta de un objeto
        idx = [cols.index(c) for c in personales]
        malos = sorted({cols[i] for f in filas for i in idx if i < len(f) and not es_ficticio(f[i])})
        if malos:
            fallas.append(f"tabla con columnas que identifican a personas o son datos sensibles y valores sin la forma ficticia de "
                          f"la guía (Persona Ficticia, 000.000.00x, @ejemplo.invalid, 399 000 000x): columnas {malos[:5]}: {ruta}")
    if privacidad:
        raros = datos_no_ficticios(texto)
        if raros:
            fallas.append(f"baterias/privacidad/ acepta solo datos con la forma ficticia de la guía; hay {raros} que no la tienen: {ruta}")
    return fallas


def datos_no_ficticios(texto):
    """Lo que encuentra el barrido de gobernanza (cédula con contexto, correo, celular, nombre con tratamiento) y no tiene
    la forma ficticia de la guía: un correo real nunca está en un dominio reservado, ninguna cédula es 000.000.00x y el
    prefijo 399 no está asignado. Devuelve {patrón: cuántos}."""
    out = {}
    for n, rx in PATRONES.items():
        k = sum(1 for m in rx.finditer(texto or "") if not ficticio_en_texto(n, m))
        if k:
            out[n] = k
    return out


# ---------------- copias temporales: el aporte con el juez de la base, y la base con las herramientas del aporte

def copiar(arbol, archivos, destino):
    for r in archivos:
        src = arbol / r
        if src.is_symlink() or not src.is_file():
            continue
        dst = destino / r
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def quitar(destino, ruta):
    q = destino / ruta.rstrip("/")
    if q.is_dir() and not q.is_symlink():
        shutil.rmtree(q)
    elif q.exists() or q.is_symlink():
        q.unlink()


def extraer(arbol, sha, rutas, destino):
    rutas = [r for r in rutas if git(arbol, "ls-tree", "--name-only", sha, "--", r).strip()]
    if rutas:
        tar = git(arbol, "archive", "--format=tar", sha, "--", *rutas, binario=True)
        with tarfile.open(fileobj=io.BytesIO(tar)) as t:
            t.extractall(destino, filter="data")


def armar_mixto(arbol, sha_base, destino):
    """Los archivos del aporte con lo confiable de la base encima: así se prueba lo que el aporte agrega con un juez
    que el aporte no pudo tocar. Queda como repositorio git, porque el SGSI pregunta qué está versionado."""
    copiar(arbol, versionables(arbol), destino)
    for c in CONFIABLES:
        quitar(destino, c)
    extraer(arbol, sha_base, [c.rstrip("/") for c in CONFIABLES], destino)
    git(destino, "init", "-q")
    git(destino, "add", "-A", "-f")
    return destino


def armar_base_con_herramientas(arbol, sha_base, destino):
    """La base entera con las herramientas del aporte, menos el banco de blindaje, que sigue siendo el de la base:
    mide si el cambio debilita una defensa con ataques que el aporte no pudo tocar."""
    extraer(arbol, sha_base, ["."], destino)
    quitar(destino, "herramientas/")
    copiar(arbol, [r for r in versionables(arbol) if r.startswith("herramientas/")], destino)
    extraer(arbol, sha_base, ["herramientas/blindaje.py"], destino)
    return destino


def evidencia_blindaje(texto, id_):
    m = re.search(rf"^[✗!] {id_} [^\n]*\n\s+(?:CEDE|ERROR): ([^\n]*)", texto, re.M)
    return m.group(1)[:160] if m else "sin evidencia"


# ---------------- el filtro

def revisar(arbol, base):
    if not arbol.is_dir():
        raise SinRevisar(f"no existe la carpeta {arbol}")
    raiz_git = Path(git(arbol, "rev-parse", "--show-toplevel").strip()).resolve()
    if raiz_git != arbol:
        raise SinRevisar(f"{arbol} no es la raíz de un repositorio git (está dentro de {raiz_git}): corre el filtro en la raíz del clon")
    elegida = base is None
    if elegida:
        base = next((b for b in ("upstream/main", "origin/main")
                     if existe_en_git(arbol, "rev-parse", "--verify", "--quiet", f"{b}^{{commit}}")), None)
        if base is None:
            raise SinRevisar("no hay upstream/main ni origin/main: trae la rama base (git fetch upstream main) o pásala con --base")
    if not existe_en_git(arbol, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"):
        raise SinRevisar(f"la base «{base}» no existe en {arbol}: tráela (git fetch) o pasa otra con --base; "
                         "el filtro no cambia de base por su cuenta")
    sha_base = git(arbol, "rev-parse", "--verify", f"{base}^{{commit}}").strip()
    # En un pull request, GitHub revisa la fusión del aporte con la base de ESE momento. Cuando la aprobación del dueño
    # llega más tarde, main ya avanzó: comparar contra el main de hoy haría ver como del aporte todo lo que entró entre
    # tanto. Se compara contra la base con la que GitHub armó la fusión (primer padre del commit de fusión) (L51), pero
    # solo si ese padre es de la rama base: desciende de la base pedida y está en origin/<rama base>. Si no se puede
    # comprobar, se queda la base pedida, que cuenta de más y nunca de menos.
    padres = git(arbol, "rev-list", "--parents", "-n", "1", "HEAD").split()
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" and len(padres) == 3 and padres[1] != sha_base:
        rama = os.environ.get("GITHUB_BASE_REF") or "main"
        if (existe_en_git(arbol, "merge-base", "--is-ancestor", sha_base, padres[1])
                and existe_en_git(arbol, "merge-base", "--is-ancestor", padres[1], f"refs/remotes/origin/{rama}")):
            sha_base = padres[1]
    punto = git(arbol, "merge-base", sha_base, "HEAD").strip()
    juez_externo = arbol not in JUEZ.parents
    archivos = cambios(arbol, punto)
    nuevos = casos_nuevos(arbol, punto, archivos)
    fallas, avisos, requiere = [], [], {}
    del_dueno = es_del_dueno()
    if punto != sha_base:
        avisos.append(f"la rama no parte de la punta de {base}: se compara contra su punto de partida ({punto[:10]}); "
                      f"actualízala con git rebase {base}")

    # rutas que en el disco de macOS caen sobre otra escrita distinto: la base, el aporte y lo que no tiene commit (L99)
    choques = colisiones([r for e, r in archivos if e != "D"], rutas_en(arbol, sha_base) | rutas_en(arbol, "HEAD")
                         | set(versionables(arbol)))
    for estado, ruta in archivos:
        c = confiable_de(ruta)
        if c:
            requiere.setdefault(c, []).append(f"{ESTADOS.get(estado, 'cambia')} {ruta}")
        if ruta in choques:
            mismas = " y ".join(f"«{g}»" for g in choques[ruta])[:200]
            texto = (f"{ruta}: en macOS y Windows {mismas} son la misma ruta (solo cambian mayúsculas, acentos o "
                     "caracteres invisibles): git deja un solo archivo en el disco y reemplaza al otro; su contenido no se revisa")
            if del_dueno:
                requiere.setdefault("rutas que chocan", []).append(f"{ESTADOS.get(estado, 'cambia')} {ruta}")
            else:
                fallas.append(texto)
            continue
        if estado == "D":
            if ruta.startswith(("baterias/", "agentes/", "DIRECTRICES")):
                avisos.append(f"borra {ruta}: lo revisa el dueño")
            continue
        motivo = motivo_prohibido(ruta)
        if motivo:
            fallas.append(motivo)
            continue
        p = arbol / ruta
        if p.is_symlink():  # un enlace hace que las herramientas lean archivos de quien abre el clon (L54)
            fallas.append(f"enlace simbólico (apunta a {os.readlink(p)}; no se aceptan: puede apuntar fuera del repositorio): {ruta}")
            continue
        if solo_del_dueno(ruta) and not del_dueno:
            # de otra persona no entran; del dueño, quedan en «requiere decisión del dueño» como todo lo de CONFIABLES
            fallas.append(f"{ruta}: los flujos de GitHub, las plantillas, CODEOWNERS y los ganchos de git solo los cambia el dueño")
        if CADENA_DEL_FILTRO.match(clave(ruta)) and not juez_externo:
            avisos.append(f"{ruta} es parte del filtro: este resultado lo da la copia del propio aporte y no prueba nada "
                          "(en GitHub juzga el de la base); el dueño revisa el cambio línea por línea")
        if not p.is_file():
            continue
        fallas += revisar_datos(ruta, p)
        if ruta.endswith(".csv"):
            if not CSV_PERMITIDOS.match(ruta):
                fallas.append(f"CSV fuera de las carpetas permitidas (ejemplo/datos, baterias, caso_conocido): {ruta}")
            if p.stat().st_size > MAX_CSV:
                fallas.append(f"CSV de más de 200 KB (los datos no se publican): {ruta}")
        if p.suffix.lower() in (".py", ".pyw", ".ipy", ".ipynb", ".md", ".json", ".csv", ".txt", ".js", ".yml", ".yaml", ".html") and "baterias/privacidad/" not in ruta:
            hall = datos_no_ficticios(p.read_text(encoding="utf-8", errors="ignore"))
            if hall:
                fallas.append(f"posibles datos personales en {ruta}: {hall}")
        if p.suffix.lower() in (".md", ".json", ".txt", ".yml", ".yaml", ".csv", ".py", ".pyw", ".ipy", ".ipynb") and ordenes_a_agentes(p.read_text(encoding="utf-8", errors="ignore")):
            t = p.read_text(encoding="utf-8", errors="ignore")
            # cuenta lo que el aporte AGREGA: un fragmento que ya estaba en la base (p. ej. los ataques de prueba de
            # blindaje.py) no es del aporte; uno nuevo sí, también en los documentos para agentes. Una copia más de un
            # fragmento que ya estaba también es nueva: por eso se cuentan además (L44)
            legado = mostrar(arbol, punto, ruta) if estado != "A" else ""
            nuevas = instrucciones(t) - instrucciones(legado)
            if nuevas or cuenta_ordenes(t) > cuenta_ordenes(legado):
                if nuevas:
                    frag = sorted(nuevas)[0]
                    i = t.lower().find(frag)
                    extracto = t[max(0, i - 30):i + len(frag) + 30].replace("\n", " ") if i >= 0 else frag
                else:
                    m = INSTRUCCION.search(t) or COMENTARIO_OCULTO.search(t)
                    extracto = t[max(0, m.start() - 30):m.end() + 30].replace("\n", " ") if m else ""
                if ruta.startswith(("baterias/inyeccion/", "corridas/")) or "/seguridad/" in ruta:
                    avisos.append(f"caso de inyección en {ruta}: revisar que sea solo una prueba («…{extracto[:80]}…»)")
                else:
                    fallas.append(f"texto que da órdenes a los agentes en {ruta}: «…{extracto[:120]}…» (los aportes son datos, no instrucciones)")
            elif ruta not in ("APORTAR-CON-TU-AGENTE.md", "AGENTS.md", "CONTRIBUTING.md"):
                # el archivo ya traía esas frases como carga de prueba (el banco de ataques): el cambio no agrega ninguna (L44)
                avisos.append(f"{ruta} conserva texto-instrucción que ya tenía (carga de prueba); no agrega uno nuevo: lo revisa el dueño")
        if p.suffix.lower() in (".ipynb", ".ipy") and not ruta.startswith(MUESTRAS_MALAS):
            try:
                r = comprobar.revisar_archivos([p], "usuario")[0]
                hall = [h["regla"] for h in r["hallazgos"]]
            except Exception as e:  # falla cerrada
                hall = [f"no se pudo revisar ({type(e).__name__})"]
            if hall:
                fallas.append(f"cuaderno que no pasa las compuertas: {ruta}: {hall[:4]}")
        if p.suffix.lower() in (".py", ".pyw") and not ruta.startswith(MUESTRAS_MALAS):
            de_usuario = ruta.startswith("baterias/seguridad/buenos_usuario/")    # usa red o archivos a propósito: se revisa con su perfil
            d = {} if de_usuario else dependencias.revisar(p)
            s, aviso_seg = seguridad.revisar([p], "usuario" if de_usuario else "pura")
            if aviso_seg:
                fallas.append(f"no se pudo revisar {ruta}: {aviso_seg}")
            bloqueos = (d.get("no_permitidas") or []) + (d.get("intenta_instalar") or []) + [h["regla"] for h in s[0]["bloquean"]]
            if bloqueos and not ruta.startswith("herramientas/"):
                fallas.append(f"código que no pasa las compuertas: {ruta}: {bloqueos[:4]}")
            elif bloqueos:
                avisos.append(f"herramienta con patrones que la compuerta marcaría: {ruta}: {bloqueos[:3]} (lo revisa el dueño)")
        if ruta.startswith(MUESTRAS_MALAS) and estado == "A":
            de_usuario = ruta.startswith("baterias/seguridad/malos_usuario/")
            d = {} if de_usuario else dependencias.revisar(p)
            s, _ = seguridad.revisar([p], "usuario" if de_usuario else "pura")
            if not (d.get("no_permitidas") or d.get("intenta_instalar") or s[0]["bloquean"]):
                avisos.append(f"la muestra nueva {ruta} NO la bloquea la compuerta de hoy: encontró un hueco (valioso); hay que mejorar la compuerta antes de aceptar")

    tmp = Path(tempfile.mkdtemp(prefix="validar-"))
    try:
        mixto = armar_mixto(arbol, sha_base, tmp / "mixto")
        # baterías de la base con los casos del aporte: una falla en un caso NUEVO es un hueco encontrado, no un error
        # unas baterías que no terminan sí son un error (L67)
        rc, out, res = correr(mixto, "herramientas/baterias.py")
        f, a = revisar_baterias(rc, out, nuevos, res)
        fallas += f
        avisos += a
        # el SGSI (sgsi/README.md): lo restringido sigue fuera, sin llaves, flujos de solo lectura y cada control con su evidencia
        rc, out, res = correr(mixto, "herramientas/sgsi.py")
        fallas += revisar_sgsi(rc, out, res)
        # la corrida sintética, verificada desde cero en una copia: no se reescribe ningún archivo del aporte
        corrida = tmp / "corrida"
        shutil.copytree(mixto / CORRIDA_REFERENCIA, corrida)
        rc, out, res = correr(mixto, "herramientas/verificar.py", str(corrida))
        if rc != 0 or not res or res.get("estado") != "aprobado":
            fallas.append(f"la corrida sintética no pasa (código {rc}): {(res or {}).get('motivos') or ultima(out)}"[:300])
        mutantes = sorted((mixto / MUTANTES).glob("m*.py"))
        rc, out, res = correr(mixto, "herramientas/verificar.py", str(corrida), "--impl", *[f"{m.stem}={m}" for m in mutantes])
        if res is None:
            fallas.append(f"mutantes: el verificador no terminó o no dejó su RESUMEN (código {rc}): {ultima(out)}")
        else:
            sin_resultado = [m.stem for m in mutantes if f"fallas_{m.stem}" not in res]
            sin_fallas = [m.stem for m in mutantes if f"fallas_{m.stem}" in res and not res[f"fallas_{m.stem}"]]
            agregadas = {Path(r).stem for e, r in archivos if e == "A" and r.startswith(MUTANTES + "/")}
            if sin_resultado:
                fallas.append(f"mutantes sin resultado del verificador: {sin_resultado}")
            for m in sin_fallas:
                if m in agregadas:
                    avisos.append(f"la mutante nueva {m} NO la atrapa el criterio: encontró un hueco del criterio (valioso)")
            viejas = [m for m in sin_fallas if m != "m00_referencia_sin_errores" and m not in agregadas]
            ref = res.get("fallas_m00_referencia_sin_errores")
            if ref is None or ref or viejas:
                fallas.append(f"el criterio da falsas alarmas o ya no atrapa mutantes que atrapaba: sin fallas = {sin_fallas}")
        # si el aporte cambia una herramienta: el banco de blindaje de la BASE contra las herramientas del aporte,
        # y las baterías con las herramientas del aporte. Lo que ceda es falla; que resista no basta (lo decide el dueño).
        if "herramientas/" in requiere:
            base_con = armar_base_con_herramientas(arbol, sha_base, tmp / "base-con-herramientas-del-aporte")
            rc, out, res = correr(base_con, "herramientas/blindaje.py")
            if res is None:
                fallas.append(f"el banco de blindaje de la base no terminó con las herramientas del aporte (código {rc}): {ultima(out)}")
            else:
                for id_ in res.get("ceden") or []:
                    fallas.append(f"el cambio debilita el blindaje: {id_}: {evidencia_blindaje(out, id_)}")
                if res.get("caja_de_arena") is False:
                    avisos.append("sin caja de arena (sandbox-exec) en esta máquina: las pruebas de red y escritura del blindaje no aplicaron")
                if rc != 0 and not res.get("ceden"):
                    fallas.append(f"el banco de blindaje salió con código {rc}: {ultima(out)}")
            rc, out, res = correr(arbol, "herramientas/baterias.py")
            if res is None:
                fallas.append(f"con las herramientas del aporte, las baterías no terminaron (código {rc}): {ultima(out)}")
            elif rc != 0:
                fallas += [f"con las herramientas del aporte, baterías: {x.get('bateria')}: {x.get('falla')}"[:300]
                           for x in (res.get("detalle") or [{"bateria": "?", "falla": f"código {rc}"}])]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    pide_dueno = [f"{c}: {', '.join(v[:6])}{' …' if len(v) > 6 else ''} "
                  f"({MOTIVO_DUENO.get(c, 'es parte de lo que juzga a los aportes')})" for c, v in requiere.items()]
    todas = fallas + [f"requiere decisión del dueño: {x}" for x in pide_dueno]
    print(f"Juez: {JUEZ} ({'de fuera del aporte' if juez_externo else 'el del propio árbol; en GitHub corre el de la base'})")
    print(f"Aporte: {len(archivos)} archivo(s) cambiados frente a {base}{' (elegida: no se pasó --base)' if elegida else ''}"
          f" · base {sha_base[:10]} · punto de partida {punto[:10]}")
    for e, r in archivos:
        print(f"  {e} {r}")
    for a in avisos:
        print(f"  · aviso: {a}")
    for f in todas:
        print(f"  ✗ {f}")
    if not todas:
        print("\n✓ pasa el filtro automático. Sigue la revisión del dueño.")
    elif not fallas:
        print("\n✗ no pasa el filtro automático: requiere decisión del dueño. El dueño revisa el cambio y decide si lo acepta.")
    else:
        print("\n✗ no pasa el filtro automático. Corrige lo marcado y vuelve a subir.")
    print("RESUMEN " + json.dumps({"fallas": todas, "avisos": avisos, "requiere_dueno": pide_dueno, "base": base,
                                   "commit_base": sha_base[:12], "punto_de_partida": punto[:12],
                                   "juez_externo": juez_externo, "revisado": True}, ensure_ascii=False))
    return 1 if todas else 0


# ---------------- prueba al filtro: aportes dañados a propósito

def _datos_personales(d):
    # se arma por partes para que el barrido no marque este archivo: el dato solo existe en el clon temporal
    (d / "ejemplo" / "contacto.md").write_text(
        "Contacto del proveedor: correo nombre.apellido" + "@" + "ejemplo.invalid, céd" + "ula 1.000.000.001 y cel. 300 000 "
        + "0001.\n", encoding="utf-8")


def _lecciones_mal_formado(d):
    p = d / "baterias/lecciones.json"
    t = p.read_text(encoding="utf-8")
    i = t.rstrip().rfind("]")
    p.write_text(t[:i] + ",\n" + t[i:], encoding="utf-8")


def _caja_hereda_entorno_y_renombre(d):
    c = d / "herramientas/caja.py"
    t = c.read_text(encoding="utf-8")
    viejo = "    e = {k: os.environ[k] for k in ENTORNO_PERMITIDO if k in os.environ}"
    if viejo not in t:
        raise ValueError("caja.py ya no tiene la línea que este caso debilita: actualiza el caso")
    c.write_text(t.replace(viejo, "    e = dict(os.environ)"), encoding="utf-8")
    v = d / "herramientas/verificar.py"
    v.write_text(v.read_text(encoding="utf-8").replace("TIEMPO_IMPL", "TIEMPO_MAX_IMPL"), encoding="utf-8")


def _juez_editado(d):
    p = d / "herramientas/validar_aporte.py"
    t = p.read_text(encoding="utf-8")
    ancla = "    todas = fallas + "
    if ancla not in t:
        raise ValueError("validar_aporte.py ya no tiene el ancla de este caso: actualiza el caso")
    p.write_text(t.replace(ancla, "    fallas.clear()\n" + ancla, 1), encoding="utf-8")
    _datos_personales(d)


def _comentario_en_herramienta(d):
    p = d / "herramientas/perfilar.py"
    p.write_text(p.read_text(encoding="utf-8") + "\n# comentario de prueba: no cambia nada\n", encoding="utf-8")


def _asistentes_flujo_y_enlace(d):
    """La revisión de L54 en el juez: configuración de asistentes y editores, un .env, un flujo de GitHub de otra
    persona y un enlace simbólico. Solo se escriben en el clon temporal: nada de esto se ejecuta."""
    (d / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")
    (d / ".vscode").mkdir()
    (d / ".vscode/tasks.json").write_text('{"version": "2.0.0", "tasks": []}\n', encoding="utf-8")
    (d / "CLAUDE.md").write_text("# notas del clon de prueba\n", encoding="utf-8")
    (d / ".env.local").write_text("VARIABLE_DE_PRUEBA=1\n", encoding="utf-8")
    (d / ".github/workflows/de_tercero.yml").write_text(
        "name: de-tercero\non: [workflow_dispatch]\npermissions:\n  contents: read\njobs: {}\n", encoding="utf-8")
    os.symlink("../README.md", d / "ejemplo/enlace.md")


def _rutas_que_chocan(d):
    """L99: el gancho de git y el flujo con otra mayúscula, armados como los arma un fork: con git update-index, sin pasar
    por el disco, que en macOS no distingue mayúsculas. skip-worktree hace que el «git add -A» del caso no los toque."""
    g = ["git", "-c", "core.quotepath=off"]
    for ruta, contenido, modo in ((".Githooks/pre-commit", "#!/bin/sh\nexit 0\n", "100755"), ("Flujo.js", "// prueba\n", "100644")):
        blob = subprocess.run([*g, "hash-object", "-w", "--stdin"], cwd=d, input=contenido.encode(), capture_output=True,  # nosec B603 B607
                              check=True).stdout.decode().strip()
        subprocess.run([*g, "update-index", "--add", "--cacheinfo", f"{modo},{blob},{ruta}"], cwd=d, check=True, capture_output=True)  # nosec B603 B607
        subprocess.run([*g, "update-index", "--skip-worktree", ruta], cwd=d, check=True, capture_output=True)  # nosec B603 B607


def _flujo_del_dueno(d):
    p = d / ".github/workflows/vigilancia-diaria.yml"
    p.write_text(p.read_text(encoding="utf-8") + "# comentario de prueba: no cambia nada\n", encoding="utf-8")


def _filas_tipo_secop(n):
    # ficticias, con la forma del extracto: así se prueba el filtro sin publicar ni un dato de SECOP
    return [{"id_contrato": f"CO1.PCCNTR.{3000000 + i}", "nit_entidad": "900000001", "codigo_entidad": "700000001",
             "nombre_entidad": "ENTIDAD PRUEBA ALFA", "fecha_de_firma": "2025-01-01T00:00:00.000", "valor_del_contrato": str(1000 + i)}
            for i in range(n)]


def _tabla_de_personas(ruta):
    # 50 personas con nombre de la guía, pero documento y celular sin la forma ficticia (10…, 300…)
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["nombre_contratista", "documento_identidad", "celular", "valor"])
        for i in range(1, 51):
            w.writerow([f"Persona Ficticia {i:02d}", f"10{i:08d}", f"300{i:07d}", 1000000 * i])


def _aporte_con_datos(d):
    """El aporte de prueba del hallazgo GOB-6: el extracto en .tsv y en .json, un caso conocido de 1.500 filas y dos
    tablas de personas, una en baterias/privacidad/ y otra en un caso_conocido/."""
    filas = _filas_tipo_secop(50_000)
    cab = list(filas[0])
    (d / "ejemplo/secop_completo.tsv").write_text("\t".join(cab) + "\n" + "".join("\t".join(f.values()) + "\n" for f in filas), encoding="utf-8")
    (d / "ejemplo/secop_completo.json").write_text(json.dumps(filas, ensure_ascii=False), encoding="utf-8")
    nueva = d / "corridas/2026-11-07-nueva/caso_conocido"
    nueva.mkdir(parents=True)
    (nueva / "contratos.csv").write_text(",".join(cab) + "\n" + "".join(",".join(f.values()) + "\n" for f in filas[:1500]), encoding="utf-8")
    _tabla_de_personas(d / "baterias/privacidad/contratistas.csv")
    _tabla_de_personas(nueva / "contratistas.csv")


def _privacidad_con_la_guia(d):
    arroba, cel = "@", "399 000 "   # por partes: este archivo no debe parecer que trae datos personales
    (d / "baterias/privacidad/caso_ficticio_nuevo.csv").write_text(
        "id,proveedor_adjudicado,documento_proveedor,correo,celular\n"
        f"P4,Persona Ficticia Cuatro,000.000.004,persona.cuatro{arroba}ejemplo.invalid,{cel}0004\n"
        f"P5,Persona Ficticia Cinco,000000005,persona.cinco{arroba}ejemplo.invalid,{cel}0005\n", encoding="utf-8")


ARCHIVOS_GOB6 = ["ejemplo/secop_completo.tsv", "ejemplo/secop_completo.json", "corridas/2026-11-07-nueva/caso_conocido/contratos.csv",
                 "baterias/privacidad/contratistas.csv", "corridas/2026-11-07-nueva/caso_conocido/contratistas.csv"]


# nombre: (preparar el clon, código esperado, textos que deben estar en las fallas, textos que no, especial)
CASOS = {
    "intacto": (None, 0, [], [], None),
    "lecciones_mal_formado": (_lecciones_mal_formado, 1, ["lecciones"], [], None),
    "caja_hereda_entorno_y_renombre": (_caja_hereda_entorno_y_renombre, 1, ["requiere decisión del dueño", "debilita el blindaje"], [], None),
    "juez_editado_y_datos_personales": (_juez_editado, 1, ["posibles datos personales", "requiere decisión del dueño"], [], None),
    "copia_sin_git": (_datos_personales, 2, [], [], "sin_git"),
    "comentario_sin_sandbox_exec": (_comentario_en_herramienta, 1, ["requiere decisión del dueño"], ["B11", "B12"], "sin_sandbox"),
    "asistentes_flujo_y_enlace": (_asistentes_flujo_y_enlace, 1, [".mcp.json", ".vscode/tasks.json", "CLAUDE.md", ".env.local",
                                  "solo los cambia el dueño", "enlace simbólico", "requiere decisión del dueño"], [], None),
    "flujo_del_dueno": (_flujo_del_dueno, 1, ["requiere decisión del dueño"], ["solo los cambia el dueño"], "del_dueno"),
    "rutas_que_chocan": (_rutas_que_chocan, 1, [".Githooks/pre-commit: en macOS y Windows «.Githooks» y «.githooks» son la misma ruta",
                                                "Flujo.js: en macOS y Windows «Flujo.js» y «flujo.js» son la misma ruta"], [], None),
    "extracto_y_personas_en_otros_formatos": (_aporte_con_datos, 1, ARCHIVOS_GOB6, [], None),
    "privacidad_con_valores_de_la_guia": (_privacidad_con_la_guia, 0, [], [], None),
}


def _probar_caso(nombre, raiz_tmp, sha):
    preparar, esperado, deben, no_deben, especial = CASOS[nombre]
    d = raiz_tmp / nombre
    g = ["git", "-c", "user.name=autoprueba", "-c", "user.email=autoprueba" + "@" + "ejemplo.invalid"]
    subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(RAIZ), str(d)], check=True, capture_output=True)  # nosec B603 B607
    for a in (["checkout", "-q", "-b", "aporte", sha], ["branch", "-f", "base-autoprueba", sha]):
        subprocess.run([*g, *a], cwd=d, check=True, capture_output=True)  # nosec B603 B607
    if preparar:
        preparar(d)
        subprocess.run([*g, "add", "-A"], cwd=d, check=True, capture_output=True)  # nosec B603 B607
        subprocess.run([*g, "commit", "-q", "-m", f"autoprueba: {nombre}"], cwd=d, check=True, capture_output=True)  # nosec B603 B607
    arbol, entorno = d, dict(os.environ)
    for k in ("GITHUB_EVENT_PATH", "GITHUB_EVENT_NAME"):   # el resultado no depende de dónde corre la autoprueba
        entorno.pop(k, None)
    if especial == "sin_git":
        arbol = raiz_tmp / f"{nombre}-copia"
        shutil.copytree(d, arbol, ignore=shutil.ignore_patterns(".git"))
    if especial == "del_dueno":   # el evento de GitHub de un pull request del dueño
        evento = raiz_tmp / f"{nombre}-evento.json"
        evento.write_text(json.dumps({"pull_request": {"author_association": "OWNER"}}), encoding="utf-8")
        entorno["GITHUB_EVENT_PATH"] = str(evento)
    if especial == "sin_sandbox":
        b = raiz_tmp / f"{nombre}-bin"
        b.mkdir()
        os.symlink(shutil.which("git"), b / "git")
        entorno["PATH"] = f"{b}{os.pathsep}/bin"
    p = subprocess.run([sys.executable, str(JUEZ), "--arbol", str(arbol), "--base", "base-autoprueba"],  # nosec B603
                       cwd=raiz_tmp, capture_output=True, text=True, env=entorno)
    res = resumen(p.stdout) or {}
    fallas = " | ".join(res.get("fallas") or [])
    problemas = []
    if p.returncode != esperado:
        problemas.append(f"salió con {p.returncode}, se esperaba {esperado}")
    problemas += [f"las fallas no mencionan «{t}»" for t in deben if t not in fallas]
    problemas += [f"las fallas mencionan «{t}»" for t in no_deben if t in fallas]
    if not res:
        problemas.append("sin RESUMEN")
    return nombre, problemas, p.returncode, (res.get("fallas") or [])[:4]


def autoprueba(argv):
    solo = set(argv[argv.index("--solo") + 1].split(",")) if "--solo" in argv else None
    nombres = [n for n in CASOS if not solo or n in solo]
    sha = git(RAIZ, "rev-parse", "HEAD").strip()
    raiz_tmp = Path(tempfile.mkdtemp(prefix="autoprueba-filtro-"))
    try:
        with ThreadPoolExecutor(3) as ex:
            resultados = list(ex.map(lambda n: _probar_caso(n, raiz_tmp, sha), nombres))
    finally:
        shutil.rmtree(raiz_tmp, ignore_errors=True)
    malos = [n for n, prob, _, _ in resultados if prob]
    for n, prob, rc, fallas in resultados:
        print(f"{'✓' if not prob else '✗'} {n}: código {rc}" + ("" if not prob else " · " + "; ".join(prob)))
        for f in fallas:
            print(f"    {f[:160]}")
    print(f"\n{len(resultados) - len(malos)} de {len(resultados)} casos dan lo esperado (clones del commit {sha[:10]}).")
    print("RESUMEN " + json.dumps({"casos": len(resultados), "fallan": malos}, ensure_ascii=False))
    return 1 if malos else 0


def main(argv):
    if "--autoprueba" in argv:
        return autoprueba(argv)
    arbol = Path(argv[argv.index("--arbol") + 1]).resolve() if "--arbol" in argv else RAIZ
    base = argv[argv.index("--base") + 1] if "--base" in argv else None
    try:
        return revisar(arbol, base)
    except SinRevisar as e:
        print(f"✗ el filtro no pudo revisar el aporte: {e}")
        print("RESUMEN " + json.dumps({"fallas": [f"sin revisar: {e}"], "avisos": [], "requiere_dueno": [], "revisado": False},
                                      ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
