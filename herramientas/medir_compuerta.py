#!/usr/bin/env python3
"""Mide la compuerta de seguridad con un lote sellado (sin IA): ¿qué parte del código vulnerable bloquea y cuántas falsas alarmas da?

Uso:
  python herramientas/medir_compuerta.py <carpeta del lote> [--perfil usuario] [--meta 0.85] [--revelar] [--salida medida.json]
  python herramientas/medir_compuerta.py <carpeta del lote> --sellar "<quién lo escribió>" "<quién revisó las etiquetas>"

Un lote sellado tiene fragmentos .py y un ETIQUETAS.json ({"f001.py": {"cwe": "CWE-89", "clase": "vulnerable"|"seguro", "tecnica": "..."}}).
Lo escribe alguien que no conoce la compuerta y vive fuera del repositorio. Los fragmentos nunca se ejecutan: solo se analizan.

Por qué sellado: si la misma persona escribe las reglas y las pruebas, o si la compuerta se califica a sí misma, la cifra sale bien
por construcción y no dice nada. Por eso:
  - sin --revelar solo se imprimen cifras por debilidad, nunca qué fragmento se escapó;
  - --revelar deja la marca REVELADO en el lote: desde ese momento el lote sirve para corregir, ya no para medir;
  - la meta se cumple con la cota inferior (95 % de confianza, una cola) y sin falsas alarmas, nunca con la cifra observada;
  - --sellar guarda la huella en baterias/sellada/MANIFIESTO.json; si después cambia un fragmento, la medida no vale.
"""
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime
from math import comb
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MANIFIESTO = AQUI.parent / "baterias" / "sellada" / "MANIFIESTO.json"
sys.path.insert(0, str(AQUI))
import seguridad  # noqa: E402

# Regla de Bandit -> debilidad, para contar si se bloqueó por la razón correcta
BANDIT_CWE = {"B608": "CWE-89", "B602": "CWE-78", "B603": "CWE-78", "B604": "CWE-78", "B605": "CWE-78", "B607": "CWE-78", "B609": "CWE-78", "B601": "CWE-78",
              "B301": "CWE-502", "B302": "CWE-502", "B403": "CWE-502", "B506": "CWE-502", "B614": "CWE-502",
              "B501": "CWE-295", "B323": "CWE-295", "B502": "CWE-295", "B503": "CWE-295", "B504": "CWE-295", "B507": "CWE-295",
              "B303": "CWE-327", "B304": "CWE-327", "B305": "CWE-327", "B324": "CWE-327", "B413": "CWE-327",
              "B105": "CWE-798", "B106": "CWE-798", "B107": "CWE-798", "B202": "CWE-22", "B701": "CWE-79", "B702": "CWE-79", "B703": "CWE-79", "B704": "CWE-79", "B308": "CWE-79"}


def cota_inferior(aciertos, n, alfa=0.05):
    """Clopper-Pearson de una cola: el menor p compatible con ver tantos aciertos."""
    if n == 0 or aciertos == 0:
        return 0.0
    bajo, alto = 0.0, 1.0
    for _ in range(60):
        p = (bajo + alto) / 2
        cola = sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(aciertos, n + 1))
        if cola > alfa:
            alto = p
        else:
            bajo = p
    return bajo


def huella(carpeta):
    h = hashlib.sha256()
    for p in sorted(carpeta.glob("*.py")) + [carpeta / "ETIQUETAS.json"]:
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def manifiesto():
    return json.loads(MANIFIESTO.read_text(encoding="utf-8")) if MANIFIESTO.exists() else {"_nota": "Huellas de los lotes sellados. Los fragmentos no se publican mientras el lote sirve de examen; revelado, pasa a las baterías.", "lotes": {}}


def sellar(carpeta, autor, revisor):
    et = json.loads((carpeta / "ETIQUETAS.json").read_text(encoding="utf-8"))
    m = manifiesto()
    m["lotes"][carpeta.name] = {"huella": huella(carpeta), "fragmentos": len(et), "vulnerables": sum(v["clase"] == "vulnerable" for v in et.values()),
                                "seguros": sum(v["clase"] == "seguro" for v in et.values()), "escribio": autor, "reviso_etiquetas": revisor,
                                "sellado": datetime.now().strftime("%Y-%m-%d %H:%M")}
    MANIFIESTO.parent.mkdir(exist_ok=True)
    MANIFIESTO.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sellado {carpeta.name}: {m['lotes'][carpeta.name]['huella'][:16]}")


def de_su_debilidad(hallazgo, cwe):
    regla = hallazgo["regla"]
    if regla.startswith("bandit "):
        return BANDIT_CWE.get(regla.split()[-1]) == cwe
    return regla.startswith(cwe + " ")


def medir(carpeta, perfil):
    et = json.loads((carpeta / "ETIQUETAS.json").read_text(encoding="utf-8"))
    rutas = [carpeta / a for a in sorted(et)]
    res, aviso = seguridad.revisar(rutas, perfil)
    if aviso:
        raise SystemExit(f"No se puede medir: {aviso}")
    por = defaultdict(lambda: {"vulnerables": 0, "bloqueados": 0, "por_su_regla": 0, "seguros": 0, "falsas_alarmas": 0})
    escapes, alarmas = [], []
    for r in res:
        nombre = Path(r["archivo"]).name
        v = et[nombre]
        fila = por[v["cwe"]]
        if v["clase"] == "vulnerable":
            fila["vulnerables"] += 1
            if r["bloquean"]:
                fila["bloqueados"] += 1
                fila["por_su_regla"] += any(de_su_debilidad(h, v["cwe"]) for h in r["bloquean"])
            else:
                escapes.append({"archivo": nombre, "cwe": v["cwe"], "tecnica": v.get("tecnica", "")})
        else:
            fila["seguros"] += 1
            if r["bloquean"]:
                fila["falsas_alarmas"] += 1
                alarmas.append({"archivo": nombre, "cwe": v["cwe"], "reglas": sorted({h["regla"] for h in r["bloquean"]})})
    return dict(por), escapes, alarmas


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    g = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    carpeta = Path(argv[0]).resolve()
    if "--sellar" in argv:
        i = argv.index("--sellar")
        sellar(carpeta, argv[i + 1], argv[i + 2])
        return 0
    perfil, meta = g("--perfil", "usuario"), float(g("--meta", "0.85"))
    marca = carpeta / "REVELADO"
    ya_revelado = marca.exists()
    por, escapes, alarmas = medir(carpeta, perfil)
    n = sum(f["vulnerables"] for f in por.values())
    bloq = sum(f["bloqueados"] for f in por.values())
    suya = sum(f["por_su_regla"] for f in por.values())
    seguros = sum(f["seguros"] for f in por.values())
    falsas = sum(f["falsas_alarmas"] for f in por.values())
    cota = cota_inferior(bloq, n)
    sello = manifiesto()["lotes"].get(carpeta.name)
    intacto = sello is None or sello["huella"] == huella(carpeta)
    cumple = cota >= meta and falsas == 0 and not ya_revelado and sello is not None and intacto
    print(f"Lote {carpeta.name} · perfil {perfil} · huella {huella(carpeta)[:16]}")
    print("| Debilidad | Bloqueó | Por su propia regla | Falsas alarmas |\n|---|---|---|---|")
    for cwe in sorted(por, key=lambda c: int(c.split("-")[1])):
        f = por[cwe]
        print(f"| {cwe} | {f['bloqueados']} de {f['vulnerables']} | {f['por_su_regla']} | {f['falsas_alarmas']} de {f['seguros']} |")
    print(f"| **Total** | **{bloq} de {n} ({bloq / n:.1%})** | {suya} ({suya / n:.1%}) | **{falsas} de {seguros}** |")
    print(f"Cota inferior con 95 % de confianza: {cota:.1%} · meta {meta:.0%}")
    if ya_revelado:
        print(f"! Este lote se reveló ({marca.read_text(encoding='utf-8').strip()}): la cifra sirve para corregir, no como medida.")
    if not intacto:
        print("! El lote cambió después de sellarlo: esta cifra no vale.")
    print(("CUMPLE" if cumple else "NO CUMPLE") + f": hace falta cota ≥ {meta:.0%}, 0 falsas alarmas y un lote sellado, intacto y sin revelar.")
    if "--revelar" in argv:
        if not ya_revelado:
            marca.write_text(datetime.now().strftime("%Y-%m-%d %H:%M") + "\n", encoding="utf-8")
        print("\nEscapes:")
        for e in escapes:
            print(f"  {e['archivo']} · {e['cwe']} · {e['tecnica']}")
        print("Falsas alarmas:")
        for a in alarmas:
            print(f"  {a['archivo']} · {a['cwe']} · {a['reglas'][:3]}")
    if g("--salida"):
        Path(g("--salida")).write_text(json.dumps({"lote": carpeta.name, "perfil": perfil, "huella": huella(carpeta), "por_debilidad": por, "bloqueados": bloq, "vulnerables": n,
                                                   "por_su_regla": suya, "seguros": seguros, "falsas_alarmas": falsas, "cota_inferior": round(cota, 4), "meta": meta, "revelado": ya_revelado,
                                                   "cumple": cumple}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if cumple else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
