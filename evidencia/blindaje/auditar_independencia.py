#!/usr/bin/env python3
"""Auditoría de independencia (sin IA): ¿algún subagente abrió lo que su ficha le prohíbe?

Uso: python evidencia/blindaje/auditar_independencia.py <carpeta de transcripciones del flujo> [...]
     python evidencia/blindaje/auditar_independencia.py --autoprueba   transcripciones ficticias, con control positivo

Lee las transcripciones (agent-*.jsonl) de una corrida orquestada, reconoce el rol de cada agente por su
instrucción y revisa cada herramienta que usó (leer archivos, comandos) contra lo que su rol no puede leer.
Hoy la independencia depende de la instrucción: esto mide si se cumple. Lo prohibido de cada rol sale de su ficha
(agentes/NN-*.md, «No puede leer»); el documentador (13) y el presentador (12) entran desde el 6-nov-2026 (L88).
"""
import json
import re
import sys
from pathlib import Path

# Lo que nadie de la etapa 3 o 4 lee: los datos crudos (datos/*.csv, junto a la corrida o en ejemplo/) y la capa limpia
CRUDOS_Y_LIMPIA = [r"datos/[^/\s\"']+\.csv", r"(?<![\w-])limpio/"]

PROHIBIDO = {
    "generador A": [r"reglas\.py", r"caso_conocido", r"sellos\.json", r"impl_b\.py"],
    "generador B": [r"reglas\.py", r"caso_conocido", r"sellos\.json", r"impl_a\.py"],
    "reparador A": [r"(?<!/)reglas\.py", r"impl_b\.py"],
    "reparador B": [r"(?<!/)reglas\.py", r"impl_a\.py"],
    "probador": [r"bitacora/[\w.-]+\.json", r"impl_a\.py", r"impl_b\.py"],
    "revisor ciego de seguridad": [r"bitacora/[\w.-]+\.json"],
    "custodio": [r"(cat|head|tail|less|sed -n|awk)[^|;&]*datos/[^ ]*\.csv", r"datos/contratos\.csv\"?\s*$"],
    # 13-documentador.md: ni los datos crudos ni la capa limpia; ni el código de los demás ni bitacora/
    "documentador": CRUDOS_Y_LIMPIA + [r"impl_a\.py", r"impl_b\.py", r"(?<![\w-])reglas\.py", r"(?<![\w-])grafico\.py",
                                       r"bitacora/[\w.-]+\.json"],
    # 12-presentador.md: ni los datos crudos ni la capa limpia; ni el código ni las bitácoras de los demás; ni las
    # hipótesis de la IA, que son historial desde el 6-nov (hipotesis.json, hipotesis_resultado.json, sus sellos)
    "presentador": CRUDOS_Y_LIMPIA + [r"impl_a\.py", r"impl_b\.py", r"(?<![\w-])reglas\.py", r"(?<![\w-])grafico\.py",
                                      r"(?<![\w-])hipotesis\.py", r"[\w-]*hipotesis[\w-]*\.json", r"bitacora/[\w.-]+\.json"],
}


PROPIA = {"probador": "3-analisis-prueba.json", "revisor ciego de seguridad": "5-gobernanza-seguridad.json",
          "documentador": "3-analisis-documentacion.json", "presentador": "4-visualizacion-presentacion.json"}


def rol(texto):
    t = texto
    for patron, nombre in [(r"Eres el GENERADOR A\b", "generador A"), (r"Eres el GENERADOR B\b", "generador B"),
                           (r"REPARADOR de [^\n]*impl_a", "reparador A"), (r"REPARADOR de [^\n]*impl_b", "reparador B"),
                           (r"Eres el PROBADOR", "probador"), (r"Eres el REVISOR DE SEGURIDAD", "revisor ciego de seguridad"), (r"Eres el CUSTODIO", "custodio"),
                           (r"Eres el DOCUMENTADOR\b", "documentador"), (r"Eres el PRESENTADOR\b", "presentador")]:
        if re.search(patron, t):
            return nombre
    return None


def usos(lineas):
    for l in lineas:
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            continue
        msg = d.get("message") or {}
        for c in (msg.get("content") or []) if isinstance(msg.get("content"), list) else []:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                i = c.get("input") or {}
                yield c.get("name"), " ".join(str(i.get(k, "")) for k in ("file_path", "command", "path", "pattern") if i.get(k))


def primera_instruccion(lineas):
    """Junta los primeros mensajes del usuario: el primero suele ser el contexto que se inyecta al iniciar."""
    textos = []
    for l in lineas:
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            continue
        msg = d.get("message") or {}
        if msg.get("role") == "user":
            c = msg.get("content")
            textos.append(c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text"))
            if len(textos) >= 4:
                break
    return "\n".join(textos)


def transcripciones(carpetas):
    """(corrida, líneas) de cada agent-*.jsonl de las carpetas."""
    for carpeta in carpetas:
        for f in sorted(Path(carpeta).glob("agent-*.jsonl")):
            yield Path(carpeta).name, f.read_text(encoding="utf-8", errors="ignore").splitlines()


def auditar(trans, prohibido=None):
    """trans: (corrida, líneas) por agente. Devuelve (agentes con rol auditado, violaciones). prohibido: la tabla de
    cada rol (por defecto, PROHIBIDO)."""
    prohibido = PROHIBIDO if prohibido is None else prohibido
    total, violaciones = 0, []
    for corrida, lineas in trans:
        r = rol(primera_instruccion(lineas))
        if not r or r not in prohibido:
            continue
        total += 1
        for herramienta, arg in usos(lineas):
            propia = PROPIA.get(r)
            for p in prohibido[r]:
                m = re.search(p, arg)
                if m and propia and propia in m.group(0):
                    continue    # su propia bitácora: la escribe y la relee, como pide su ficha
                if m and not re.search(r"(seguridad|dependencias|verificar|verificar_hipotesis|validar_aporte)\.py", arg):
                    violaciones.append({"corrida": corrida, "rol": r, "herramienta": herramienta, "uso": arg[:180]})
    return total, violaciones


def autoprueba():
    """Transcripciones ficticias del documentador y del presentador: lo que su ficha permite no se marca; lo que prohíbe,
    sí. Control positivo: con la tabla de antes (sin esos dos roles) las mismas transcripciones no se auditaban."""
    C = "corridas/una-corrida"
    ruta = lambda r: f"{C}/{r}"                                          # noqa: E731

    def transcripcion(instruccion, usos_):
        lineas = [{"message": {"role": "user", "content": instruccion}}]
        for nombre, entrada in usos_:
            lineas.append({"message": {"role": "assistant", "content": [{"type": "tool_use", "name": nombre, "input": entrada}]}})
        return [json.dumps(x, ensure_ascii=False) for x in lineas]

    leer = lambda r: ("Read", {"file_path": r})                          # noqa: E731
    correr = lambda cmd: ("Bash", {"command": cmd})                      # noqa: E731
    permitidos = {
        "documentador": [leer(ruta("spec.json")), leer(ruta("informe.json")), leer(ruta("datos/procedencia_contratos.json")),
                         leer(ruta("limpieza_contratos.json")), leer(ruta("gobernanza.json")), leer(ruta("grafico.json")),
                         leer(ruta("grafico_verificacion.json")), correr(f"python herramientas/validar_whitepaper.py {C}"),
                         correr(f"python herramientas/whitepaper_corrida.py {C}"), leer(ruta("bitacora/3-analisis-documentacion.json"))],
        "presentador": [leer(ruta("informe.json")), leer(ruta("spec.json")), leer(ruta("grafico.json")),
                        leer(ruta("grafico_verificacion.json")), leer(ruta("datos/procedencia_contratos.json")),
                        leer("baterias/lecciones.json"), correr(f"python herramientas/verificar_presentacion.py {C}"),
                        correr(f"python herramientas/verificar_grafico.py {C}"), leer(ruta("bitacora/4-visualizacion-presentacion.json"))],
    }
    prohibidos = {
        "documentador": [leer(ruta("datos/contratos.csv")), correr("head -5 " + ruta("limpio/contratos.csv")), leer(ruta("impl_a.py")),
                         leer(ruta("impl_b.py")), leer(ruta("reglas.py")), leer(ruta("grafico.py")),
                         leer(ruta("bitacora/2-procesamiento-generador-a.json")), leer("ejemplo/datos/ventas.csv")],
        "presentador": [leer(ruta("datos/contratos.csv")), leer(ruta("limpio/contratos.csv")), leer(ruta("impl_b.py")),
                        leer(ruta("reglas.py")), leer(ruta("grafico.py")), leer(ruta("hipotesis_resultado.json")),
                        leer(ruta("hipotesis.json")), leer(ruta("sellos_hipotesis.json")), leer(ruta("hipotesis.py")),
                        correr("cat " + ruta("bitacora/3-analisis-documentacion.json"))],
    }
    instruccion = {"documentador": "Eres el DOCUMENTADOR (etapa 3 · Análisis).",
                   "presentador": "Eres el PRESENTADOR (etapa 4 · Visualización)."}
    malos = []
    bien = [("ficticia", transcripcion(instruccion[r_], usos_)) for r_, usos_ in permitidos.items()]
    total, v = auditar(bien)
    ok = total == 2 and not v
    print(f"{'✓' if ok else '✗'} lo que permiten sus fichas no se marca: {total} agentes, {len(v)} usos prohibidos"
          + (f" — falsas alarmas: {[x['uso'] for x in v]}" if v else ""))
    malos += [] if ok else ["falsas alarmas o rol no reconocido"]
    for r_, usos_ in prohibidos.items():
        for u in usos_:
            _, v = auditar(bien + [("ficticia", transcripcion(instruccion[r_], [u]))])
            ok = len(v) == 1 and v[0]["rol"] == r_
            print(f"{'✓' if ok else '✗'} {r_} · {u[1].get('file_path') or u[1].get('command')}: "
                  f"{'se marca' if ok else 'NO se marca'}")
            if not ok:
                malos.append(f"{r_}: {u[1]}")
    # control positivo (L27): con la tabla de antes del 6-nov, un documentador que lee impl_a.py no se auditaba
    mal = [("ficticia", transcripcion(instruccion["documentador"], [leer(ruta("impl_a.py"))]))]
    antes = {k: v for k, v in PROHIBIDO.items() if k not in ("documentador", "presentador")}
    t_antes, v_antes = auditar(mal, antes)
    t_hoy, v_hoy = auditar(mal)
    ok = not v_antes and len(v_hoy) == 1
    print(f"{'✓' if ok else '✗'} control positivo: con la tabla de antes, {t_antes} agentes auditados y "
          f"{len(v_antes)} usos prohibidos; hoy, {t_hoy} y {len(v_hoy)}")
    malos += [] if ok else ["control positivo"]
    casos = 1 + sum(len(x) for x in prohibidos.values()) + 1
    print("RESUMEN " + json.dumps({"autoprueba": "aprobada" if not malos else "fallida", "casos": casos, "fallas": malos},
                                  ensure_ascii=False))
    return 1 if malos else 0


def main(carpetas):
    if "--autoprueba" in carpetas:
        return autoprueba()
    total, violaciones = auditar(transcripciones(carpetas))
    print(f"Agentes con rol auditado: {total} · usos prohibidos: {len(violaciones)}")
    for v in violaciones[:40]:
        print(f"  ✗ [{v['corrida']}] {v['rol']} · {v['herramienta']}: {v['uso']}")
    print("RESUMEN " + json.dumps({"agentes": total, "violaciones": len(violaciones)}, ensure_ascii=False))
    return 1 if violaciones else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
