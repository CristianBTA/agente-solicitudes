"""Recoge, para el dueño, lo que dejaron los grill-me en los forks: harness/<usuario>.md y grill-me/<usuario>.md.

  GH_TOKEN=$(gh auth token) .venv/bin/python herramientas/recoger_grill.py [--salida fuentes/grill]   # el Python del entorno trae los certificados

Recorre los forks públicos del repositorio por la API de GitHub. En cada fork busca la carpeta harness/ en la rama «harness»
y la carpeta grill-me/ en la rama «grill-me» (modo A de las guías) y, si no están, en su rama principal (modo B, desde la web).
Guarda cada archivo en <salida>/<carpeta>/<dueño-del-fork>__<archivo> (fuentes/ no se versiona), lo pasa por
revisar_grill.py (sin IA) y escribe <salida>/indice.json con lo que pasó y lo que no. No ejecuta nada de lo que descarga:
solo lee texto. Sin GH_TOKEN funciona con el límite anónimo de GitHub (60 consultas por hora), que alcanza para pocos forks.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revisar_grill  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
REPO = "CristianBTA/subagentes-big-data"
API = "https://api.github.com"
CARPETAS = {"harness": "harness", "grill-me": "grill-me"}   # carpeta → rama del modo A
SEGURO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
MAX_BYTES = revisar_grill.MAX_BYTES
MAX_JSON = 10_000_000


def pedir(url, crudo=False):
    if not url.startswith((API + "/", "https://raw.githubusercontent.com/")):
        raise ValueError("solo se consulta la API y el contenido crudo de GitHub")
    cab = {"Accept": "application/vnd.github.raw" if crudo else "application/vnd.github+json", "User-Agent": "recoger-grill"}
    if os.environ.get("GH_TOKEN"):
        cab["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=30) as r:  # nosec B310: URL fija de GitHub
            datos = r.read(MAX_BYTES + 1 if crudo else MAX_JSON)   # el tope de 40 KB es para los archivos, no para la API
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    return datos if crudo else json.loads(datos)


def forks():
    out, pagina = [], 1
    while True:
        lote = pedir(f"{API}/repos/{REPO}/forks?per_page=100&page={pagina}") or []
        out += [(f["full_name"], f["owner"]["login"], f["default_branch"]) for f in lote]
        if len(lote) < 100:
            return out
        pagina += 1


def main(argv):
    salida = RAIZ / (argv[argv.index("--salida") + 1] if "--salida" in argv else "fuentes/grill")
    indice = []
    lista = forks()
    print(f"{len(lista)} forks de {REPO}")
    for nombre, dueno, principal in lista:
        if not SEGURO.match(dueno):
            continue
        for carpeta, rama in CARPETAS.items():
            for ref in dict.fromkeys((rama, principal)):
                q = urllib.parse.quote
                items = pedir(f"{API}/repos/{q(nombre)}/contents/{carpeta}?ref={q(ref)}")
                if not isinstance(items, list):
                    continue
                for it in items:
                    if it.get("type") != "file" or not it["name"].endswith(".md") or not SEGURO.match(it["name"]):
                        continue
                    if it.get("size", 0) > MAX_BYTES:
                        indice.append({"fork": nombre, "rama": ref, "archivo": f"{carpeta}/{it['name']}", "pasa": False,
                                       "fallas": [f"pesa {it['size']} bytes"]})
                        continue
                    datos = pedir(f"{API}/repos/{q(nombre)}/contents/{carpeta}/{q(it['name'])}?ref={q(ref)}", crudo=True)
                    if datos is None:
                        continue
                    destino = salida / carpeta / f"{dueno}__{it['name']}"
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    destino.write_bytes(datos[:MAX_BYTES + 1])
                    # revisar_grill mira la carpeta y el nombre: se revisa una copia con el nombre que tiene en el fork
                    prueba = salida / ".revision" / carpeta / it["name"]
                    prueba.parent.mkdir(parents=True, exist_ok=True)
                    prueba.write_bytes(datos[:MAX_BYTES + 1])
                    _, fallas, avisos, secciones = revisar_grill.revisar(prueba)
                    prueba.unlink()
                    indice.append({"fork": nombre, "rama": ref, "archivo": f"{carpeta}/{it['name']}", "guardado": str(destino.relative_to(RAIZ)),
                                   "pasa": not fallas, "fallas": fallas, "avisos": avisos, "secciones": secciones})
                    print(("✓" if not fallas else "✗"), nombre, ref, f"{carpeta}/{it['name']}", "; ".join(fallas)[:160])
                break   # si la rama del modo A trae la carpeta, no se mira la principal
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    por = {c: sum(1 for x in indice if x["archivo"].startswith(c + "/") and x["pasa"]) for c in CARPETAS}
    print(f"RESUMEN: {len(indice)} archivo(s) · harness que pasan: {por['harness']} · grill-me que pasan: {por['grill-me']} · índice en {salida / 'indice.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
