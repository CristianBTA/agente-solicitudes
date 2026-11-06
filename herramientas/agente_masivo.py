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
  7. validación sin IA: validar_ficha.py por ficha, SIN caché y contra la fuente real → <trabajo>/RESULTADO.md.
Después de esto, el juicio de valor lo hacen un juez ciego y las personas: el validador mide la forma, no el valor.
"""
import json
import os
import shutil
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


def resumen(texto):
    for linea in reversed(texto.splitlines()):
        if linea.startswith("RESUMEN "):
            try:
                return json.loads(linea[8:])
            except ValueError:
                return None
    return None


def main(argv):
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
            print(f"6. IA: {motor} escribe las fichas (puede tardar)…", flush=True)
            subprocess.run(motores[motor], cwd=trabajo)  # nosec B603
        else:
            if motor != "ninguno":
                print(f"   (no se encontró la CLI de {motor}: se imprime el texto)", flush=True)
            print("6. IA: pega esto en la IA que uses, con acceso a la carpeta de trabajo:\n\n" + pedido + "\n")
            if "--validar" not in argv:
                return 0

    print("7. validación sin IA, contra la fuente real y sin caché…", flush=True)
    filas = []
    for f in sorted(fichas.glob("*.json")):
        if f.name.endswith((".dictamen.json", ".verificacion.json")):
            continue
        rc, out = correr(AQUI / "validar_ficha.py", f, "--inventario", inventario, salida=f.with_suffix(".log"))
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
    print(f"RESUMEN {json.dumps({'fichas': len(filas), 'pasan': ok})}")
    return 0 if filas and ok == len(filas) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
