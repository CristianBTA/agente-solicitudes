"""Rutas portables: las specs selladas guardan rutas absolutas de la máquina donde se corrieron.
En un clon, cada ruta se busca de nuevo dentro de la carpeta del repositorio (lo que viene después de
«agente-solicitudes/»), sin tocar los archivos sellados."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCA = "agente-solicitudes/"


def resolver(ruta):
    # Primero la copia de ESTE repositorio: con dos clones en la misma máquina (el del dueño y el que revisa un aporte,
    # o un worktree), la ruta absoluta sellada existe pero apunta al OTRO clon; verificar contra esos archivos rompe el
    # linaje (y la caja de arena, con razón, no deja leerlos).
    s = str(ruta)
    if MARCA in s:
        q = RAIZ / s.split(MARCA, 1)[1]
        if q.exists():
            return str(q)
    return str(Path(ruta))


def resolver_datos(spec):
    spec["datos"] = {t: resolver(r) for t, r in spec["datos"].items()}
    if spec.get("datos_crudos"):   # también el crudo: las hipótesis y las reglas leen de ahí (L-rutas-crudos)
        spec["datos_crudos"] = {t: resolver(r) for t, r in spec["datos_crudos"].items()}
    return spec


def procedencias(c, spec):
    """La procedencia de CADA tabla de la spec: procedencia_<tabla>.json en la carpeta datos/ de la corrida o junto a su
    dato crudo (o al limpio). Con varias tablas, ninguna reemplaza a otra. {tabla: procedencia, o None si no hay}.
    De corridas viejas se acepta el procedencia.json genérico solo si dice que es de esa tabla."""
    import json
    crudos = spec.get("datos_crudos") or {}
    out = {}
    for t in spec.get("datos") or {}:
        carpetas = [Path(c) / "datos"] + [Path(resolver(r)).parent for r in (crudos.get(t), spec["datos"].get(t)) if r]
        p = next((d / f"procedencia_{t}.json" for d in carpetas if (d / f"procedencia_{t}.json").exists()), None)
        out[t] = json.loads(p.read_text(encoding="utf-8")) if p else None
        if out[t] is None:
            for d in carpetas:
                g = d / "procedencia.json"
                if g.exists():
                    viejo = json.loads(g.read_text(encoding="utf-8"))
                    if viejo.get("tabla") == t:
                        out[t] = viejo
                        break
    return out


def estado_ingesta(procs):
    """True si TODAS las tablas tienen una procedencia aprobada; False si alguna falta o fue rechazada; None si ninguna
    pasó por la ingesta con contrato (p. ej. datos sintéticos versionados)."""
    if not procs or not any(procs.values()):
        return None
    return all(p and p.get("estado") == "aprobada" for p in procs.values())


def autoprueba():
    """Una spec sellada en otra máquina debe resolver datos Y datos_crudos a la copia de este clon."""
    import json
    otra = "/otra/maquina/agente-solicitudes/ejemplo/datos/ventas.csv"
    spec = resolver_datos({"datos": {"t": otra}, "datos_crudos": {"t": otra}})
    propia = str(RAIZ / "ejemplo/datos/ventas.csv")
    ok = spec["datos"]["t"] == propia and spec["datos_crudos"]["t"] == propia
    print(("✓" if ok else "✗") + " datos y datos_crudos de una spec sellada en otra máquina apuntan a la copia de este clon")
    print("RESUMEN " + json.dumps({"autoprueba": ok}))
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(autoprueba() if "--autoprueba" in sys.argv else 0)
