#!/usr/bin/env python3
"""Rutas que un aporte no puede tocar sin el dueño. Corre la versión de main y nunca el código del aporte.

El filtro de aportes (validar_aporte.py) corre la copia del propio pull request: si el aporte lo cambia, cambia lo que
importa o agrega un módulo que reemplaza a uno de los que importan las herramientas, el verde no prueba nada (L54).
Este chequeo corre en GitHub con pull_request_target, o sea con la versión de main, y el aporte no puede cambiarlo.
No descarga ni ejecuta el código del aporte: recibe solo los nombres de los archivos que cambia (API de GitHub).

Uso:
  gh api --paginate repos/R/pulls/N/files --jq '.[] | {f: .filename, p: .previous_filename} | @json' \\
      | python3 herramientas/rutas_protegidas.py --autor OWNER --esperados 7
  python3 herramientas/rutas_protegidas.py --autoprueba
Solo biblioteca estándar.
"""
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# El filtro, lo que importa y lo que corre para decidir, más los flujos de GitHub (incluido este chequeo).
FILTRO = re.compile(r"^(herramientas/(validar_aporte|rutas_protegidas|gobernanza|seguridad|dependencias|blindaje|sgsi|caja"
                    r"|integridad)\.py|herramientas/permitidas\.json|requirements\.txt|\.github/.+)$")
# Python los carga solo al arrancar, antes de cualquier herramienta.
ARRANQUE = re.compile(r"(^|/)(sitecustomize|usercustomize)\.py$|\.pth$")


def nombres_que_reemplazan():
    """Módulos que importan las herramientas: biblioteca estándar y las librerías permitidas (por su nombre de import)."""
    nombres = set(sys.stdlib_module_names)
    try:
        perm = json.loads((RAIZ / "herramientas/permitidas.json").read_text(encoding="utf-8"))["permitidas"]
        nombres |= {k.lower() for k in perm} | {v.get("import", "").lower() for v in perm.values()}
    except Exception:
        pass
    return nombres - {""}


def decidir(archivos, autor, esperados=None):
    """archivos: lista de {"f": ruta, "p": ruta anterior o None}. Devuelve (tocadas, bloquea, problemas_de_entrada)."""
    entrada = []
    if esperados is not None and len(archivos) < esperados:
        entrada.append(f"la API entregó {len(archivos)} de {esperados} archivos: no se puede revisar todo el aporte")
    reemplazan = nombres_que_reemplazan()
    tocadas = []
    for a in archivos:
        for r in {a.get("f"), a.get("p")} - {None, ""}:
            if FILTRO.match(r):
                tocadas.append((r, "el filtro de aportes, lo que corre o los flujos de GitHub"))
            elif ARRANQUE.search(r):
                tocadas.append((r, "Python lo carga solo al arrancar"))
            else:
                m = re.match(r"^herramientas/([^/]+?)(\.py|/.*)?$", r)
                if m and m.group(1).lower() in reemplazan:
                    tocadas.append((r, f"reemplaza el módulo «{m.group(1)}» que importan las herramientas"))
    bloquea = bool(entrada) or (bool(tocadas) and autor != "OWNER")
    return sorted(set(tocadas)), bloquea, entrada


def leer_entrada(texto):
    archivos = []
    for n, linea in enumerate(texto.splitlines(), 1):
        if not linea.strip():
            continue
        d = json.loads(linea)  # una línea que no es JSON detiene todo (falla cerrada)
        if not isinstance(d, dict) or not isinstance(d.get("f"), str):
            raise ValueError(f"línea {n} sin ruta")
        archivos.append({"f": d["f"], "p": d.get("p") if isinstance(d.get("p"), str) else None})
    return archivos


def main(argv):
    if "--autoprueba" in argv:
        return autoprueba()
    autor = argv[argv.index("--autor") + 1] if "--autor" in argv else ""
    esperados = int(argv[argv.index("--esperados") + 1]) if "--esperados" in argv else None
    try:
        archivos = leer_entrada(sys.stdin.read())
    except Exception as e:
        print(f"✗ no se pudo leer la lista de archivos ({type(e).__name__}): no se aprueba lo que no se revisó")
        return 1
    tocadas, bloquea, entrada = decidir(archivos, autor, esperados)
    lineas = [f"Aporte: {len(archivos)} archivo(s); autor: {autor or 'desconocido'}"]
    lineas += [f"  ✗ {e}" for e in entrada]
    lineas += [f"  {'·' if autor == 'OWNER' else '✗'} {r}: {por}" for r, por in tocadas]
    if bloquea:
        lineas.append("✗ El aporte toca el filtro, lo que corre o los flujos de GitHub: solo los cambia el dueño. "
                      "Quita esos archivos del pull request (si encontraste un hueco del filtro, abre un issue).")
    else:
        lineas.append("✓ " + ("Es del dueño: los cambios marcados los revisa él." if tocadas else "No toca rutas protegidas."))
    print("\n".join(lineas))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("```\n" + "\n".join(lineas) + "\n```\n")
    print("RESUMEN " + json.dumps({"archivos": len(archivos), "tocadas": [r for r, _ in tocadas], "bloquea": bloquea},
                                  ensure_ascii=False))
    return 1 if bloquea else 0


def autoprueba():
    """Cada caso con lo que debe pasar; más todas las herramientas de hoy, que un tercero sí puede mejorar."""
    T, D = "CONTRIBUTOR", "OWNER"
    casos = [
        ("edita el filtro", [{"f": "herramientas/validar_aporte.py"}], T, True),
        ("edita lo que importa el filtro", [{"f": "herramientas/gobernanza.py"}], T, True),
        ("agrega un flujo de GitHub", [{"f": ".github/workflows/x.yml"}], T, True),
        ("edita este chequeo", [{"f": "herramientas/rutas_protegidas.py"}], T, True),
        ("cambia las dependencias", [{"f": "requirements.txt"}], T, True),
        ("reemplaza un módulo estándar", [{"f": "herramientas/unicodedata.py"}], T, True),
        ("reemplaza un módulo con una carpeta", [{"f": "herramientas/json/__init__.py"}], T, True),
        ("reemplaza una librería permitida", [{"f": "herramientas/pandas.py"}], T, True),
        ("sitecustomize", [{"f": "herramientas/sitecustomize.py"}], T, True),
        ("archivo .pth", [{"f": "a.pth"}], T, True),
        ("renombra el filtro para sacarlo", [{"f": "herramientas/viejo.py", "p": "herramientas/validar_aporte.py"}], T, True),
        ("la API entrega menos archivos de los que dice el pull request", [{"f": "agentes/x.md"}], T, True, 3),
        ("aporte normal", [{"f": "agentes/13-x.md"}, {"f": "baterias/fechas/casos.json"}, {"f": "herramientas/color.py"}], T, False),
        ("herramienta nueva con nombre propio", [{"f": "herramientas/recorrer_partes.py"}], T, False),
        ("el dueño toca el filtro", [{"f": "herramientas/validar_aporte.py"}, {"f": ".github/workflows/x.yml"}], D, False),
    ]
    malos = []
    for c in casos:
        nombre, archivos, autor, debe = c[:4]
        _, bloquea, _ = decidir(archivos, autor, c[4] if len(c) > 4 else len(archivos))
        ok = bloquea == debe
        print(f"{'✓' if ok else '✗'} {nombre}: {'bloquea' if bloquea else 'pasa'}")
        if not ok:
            malos.append(nombre)
    hoy = [str(p.relative_to(RAIZ)) for p in sorted((RAIZ / "herramientas").glob("*.py"))]
    falsas = [h for h in hoy if not FILTRO.match(h) and decidir([{"f": h}], T)[1]]
    print(f"{'✓' if not falsas else '✗'} {len(hoy)} herramientas de hoy: un tercero puede mejorar las que no son del filtro"
          + (f" — falsas alarmas: {falsas}" if falsas else ""))
    for nombre, texto in (("línea que no es JSON", "esto no es json\n"), ("línea sin ruta", '{"p": "x"}\n')):
        try:
            leer_entrada(texto)
            malos.append(nombre)
            print(f"✗ {nombre}: se aceptó")
        except Exception:
            print(f"✓ {nombre}: se detiene")
    print("RESUMEN " + json.dumps({"autoprueba": "aprobada" if not (malos or falsas) else "fallida", "casos": len(casos) + 3,
                                   "fallas": malos + falsas}, ensure_ascii=False))
    return 1 if malos or falsas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
