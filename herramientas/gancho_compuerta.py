#!/usr/bin/env python3
"""Gancho de Claude Code: el código que no pasa la compuerta no se entrega (sin IA).

Se configura en un subagente o en los ajustes del usuario (ver conexion/claude-code/README.md); lee por la entrada estándar el JSON del gancho.
  - PostToolUse (Write, Edit, NotebookEdit): revisa el archivo. Si no pasa, sale con 2 y el motivo le vuelve al modelo para que corrija.
  - Stop o SubagentStop: revisa todo lo que tocó el agente, también lo que escribió por Bash si es un repositorio git. Si algo no pasa, sale con 2
    y el agente sigue trabajando. Después de 2 rondas lo deja parar, pero antes pone esos archivos en cuarentena (.bloqueado): lo que no pasa no se
    entrega, y lo que siga decide una persona.
Si la compuerta no puede revisar (falta Bandit, archivo ilegible), cuenta como que no pasa: nunca se da por bueno sin revisión.

COMPUERTA_PERFIL=usuario|pura elige el perfil. COMPUERTA_EXCLUIR es una lista de carpetas completas, separadas por coma, que no se revisan.
COMPUERTA_BITACORA=<archivo> deja una línea por decisión (evento, archivo y resultado), para poder comprobar que el gancho sí actuó.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comprobar  # noqa: E402

RONDAS = 2
HERRAMIENTAS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
LISTAS_FIJAS = {"permitidas_usuario.json", "permitidas.json"}    # solo las cambia una persona, fuera del gancho


def perfil():
    return os.environ.get("COMPUERTA_PERFIL", "usuario")


def anota(evento, archivo, resultado, motivo=""):
    ruta = os.environ.get("COMPUERTA_BITACORA")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"hora": datetime.now().strftime("%H:%M:%S"), "evento": evento, "archivo": Path(archivo).name, "resultado": resultado, "motivo": motivo[:200]}, ensure_ascii=False) + "\n")


def _sin_seguir_enlace(ruta, raiz):
    """Ruta absoluta sin resolver el último tramo: un enlace que apunta a una carpeta excluida no hereda la exclusión."""
    p = Path(raiz) / ruta
    return p.parent.resolve() / p.name


def _dentro(ruta, carpetas):
    """¿La ruta relativa está dentro de alguna carpeta? Compara carpetas completas: «test» no cubre test_etl.py ni testimonios/."""
    return any(ruta == c or ruta.startswith(c + "/") for c in (x.strip().strip("/") for x in carpetas) if c)


def excluido(ruta, raiz):
    abs_ = _sin_seguir_enlace(ruta, raiz)
    repo = AQUI.parent     # las carpetas propias de este repositorio solo valen en él, no en los proyectos ajenos
    if abs_.is_relative_to(repo) and abs_.relative_to(repo).as_posix().startswith(comprobar.EXCLUIDAS_REPO):
        return True
    raiz_abs = Path(raiz).resolve()
    if not abs_.is_relative_to(raiz_abs):
        return False
    return _dentro(abs_.relative_to(raiz_abs).as_posix(), os.environ.get("COMPUERTA_EXCLUIR", "").split(","))


def _estado_ruta(ev):
    clave = f"{ev.get('session_id', 'sin-sesion')}:{ev.get('agent_id', 'principal')}"
    return Path(tempfile.gettempdir()) / f"compuerta-{hashlib.sha256(clave.encode()).hexdigest()[:20]}.json"


def leer_estado(ev):
    try:
        return json.loads(_estado_ruta(ev).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"archivos": [], "rondas": 0}


def guardar_estado(ev, st):
    _estado_ruta(ev).write_text(json.dumps(st), encoding="utf-8")


def problemas(rutas):
    """Devuelve {archivo: texto del motivo} con lo que no pasa. Lo que no se puede revisar también cuenta."""
    if not rutas:
        return {}
    try:
        res = comprobar.revisar_archivos(rutas, perfil())
    except Exception as e:  # falla cerrada: una revisión que se cae no aprueba nada
        return {r: f"no se pudo revisar ({type(e).__name__}: {e})" for r in rutas}
    salida = {}
    for r in res:
        if not r["pasa"]:
            salida[r["archivo"]] = "; ".join(f"{h['linea']}: {h['regla']} ({h['detalle']})" for h in r["hallazgos"][:8])
    return salida


def tocados_por_git(raiz):
    """Código con cambios sin commit, desde la raíz del repositorio, también en subcarpetas, submódulos y repos anidados.
    Devuelve [] si no hay repositorio y None si git falla o tarda: eso nunca cuenta como «nada que revisar»."""
    def git(*a):
        return subprocess.run(["git", "-C", str(raiz), "-c", "core.quotepath=off", *a], capture_output=True, timeout=20)  # nosec B603 B607
    try:
        top = git("rev-parse", "--show-toplevel")
        if top.returncode != 0:
            hay_git = any((d / ".git").exists() for d in [Path(raiz).resolve(), *Path(raiz).resolve().parents])
            return [] if b"not a git repository" in top.stderr and not hay_git else None
        p = git("status", "--porcelain", "-z", "--untracked-files=all")
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    base = Path(os.fsdecode(top.stdout).rstrip("\n"))
    campos = [os.fsdecode(x) for x in p.stdout.split(b"\0")]
    salida, i = [], 0
    while i < len(campos):
        c = campos[i]
        i += 1
        if len(c) < 4:
            continue
        estado, ruta = c[:2], c[3:]
        if estado[0] in "RC":
            i += 1      # con -z, tras un renombrado viene la ruta de origen
        if "D" in estado:
            continue
        destino = base / ruta
        if destino.is_dir():        # repo anidado o submódulo: git lo muestra como carpeta
            salida += [str(x) for x in comprobar.recoger([str(destino)])[0]]
        elif comprobar.es_codigo(ruta):
            salida.append(str(destino))
    return salida


def al_escribir(ev, raiz):
    if ev.get("tool_name") not in HERRAMIENTAS:
        return 0
    entrada = ev.get("tool_input") or {}
    ruta = entrada.get("file_path") or entrada.get("notebook_path") or ""
    if Path(ruta).name in LISTAS_FIJAS:
        st = leer_estado(ev)
        st["lista_tocada"] = True
        guardar_estado(ev, st)
        anota("al guardar", ruta, "bloqueado", "lista de librerías")
        print("La compuerta rechaza este cambio: la lista de librerías permitidas no se edita desde un asistente. Qué se hace: devolver el archivo como estaba, usar una librería ya permitida o decirle a la persona responsable qué se necesita.", file=sys.stderr)
        return 2
    if not comprobar.es_codigo(ruta) or excluido(ruta, raiz):
        anota("al guardar", ruta or "(sin ruta)", "sin revisar: no es código o está excluido")
        return 0
    ruta = str(Path(raiz) / ruta)
    st = leer_estado(ev)
    if ruta not in st["archivos"]:
        st["archivos"].append(ruta)
        guardar_estado(ev, st)
    mal = problemas([ruta])
    if mal:
        anota("al guardar", ruta, "bloqueado", mal[ruta])
        print(f"La compuerta bloqueó {Path(ruta).name}: {mal[ruta]}. Corrige la causa y vuelve a guardar; no silencies la regla.", file=sys.stderr)
        return 2
    anota("al guardar", ruta, "pasa")
    # Se confirma al modelo: sin esta línea no puede distinguir «pasó» de «el gancho no corrió», y ese silencio ya engañó una vez
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": f"La compuerta revisó {Path(ruta).name}: pasa."}}, ensure_ascii=False))
    return 0


def al_parar(ev, raiz):
    st = leer_estado(ev)
    de_git = tocados_por_git(raiz)
    candidatos = set(st["archivos"]) | set(de_git or [])
    rutas = sorted(r for r in candidatos if Path(r).is_file() and comprobar.es_codigo(r) and not excluido(r, raiz))
    mal = problemas(rutas)
    fijos = {}
    if de_git is None:
        fijos["git"] = "git falló o tardó y no se pudo saber qué cambió, así que no se da por revisado. Qué se hace: arreglar el repositorio o pedirle a una persona que revise"
    if st.get("lista_tocada"):
        fijos["lista de librerías"] = "se editó en esta sesión. Qué se hace: devolverla como estaba; la cambia una persona"
    if not mal and not fijos:
        anota("al terminar", ", ".join(Path(r).name for r in rutas) or "(nada)", "pasa")
        return 0
    st["rondas"] = st.get("rondas", 0) + 1
    guardar_estado(ev, st)
    if st["rondas"] <= RONDAS:
        detalle = " | ".join(f"{Path(r).name}: {m}" for r, m in {**mal, **fijos}.items())
        anota("al terminar", ", ".join(Path(r).name for r in {**mal, **fijos}), f"bloqueado, ronda {st['rondas']}", detalle)
        print(f"No se puede entregar todavía (ronda {st['rondas']} de {RONDAS}). {detalle}. Corrige la causa; si crees que la regla está mal, dilo en tu respuesta, pero no entregues ese código.", file=sys.stderr)
        return 2
    apartados, sin_apartar = [], list(fijos)
    for r in mal:
        destino = r + ".bloqueado"
        try:
            os.replace(r, destino)
            apartados.append(Path(destino).name)
        except OSError:
            sin_apartar.append(Path(r).name)
    anota("al terminar", ", ".join(apartados + sin_apartar), "cuarentena")
    if sin_apartar and st["rondas"] <= RONDAS + 2:      # no quedó aparte ni revisado: todavía no se aprueba
        print(f"No se puede entregar: {', '.join(sin_apartar)} sigue sin revisar o sin apartar. {' | '.join(fijos.values())} Lo decide una persona; dilo en tu respuesta.", file=sys.stderr)
        return 2
    if sin_apartar:
        print(json.dumps({"systemMessage": f"Compuerta: {', '.join(sin_apartar)} sigue sin revisar o sin apartar; no se da por bueno. Lo decide una persona."}, ensure_ascii=False))
        return 0
    print(json.dumps({"systemMessage": f"Compuerta: {len(mal)} archivo(s) no pasaron tras {RONDAS} rondas y quedaron en cuarentena: {', '.join(apartados)}. Lo decide una persona."}, ensure_ascii=False))
    return 0


def main():
    try:
        ev = json.load(sys.stdin)
    except ValueError as e:
        print(f"El gancho de la compuerta no entendió la entrada: {e}", file=sys.stderr)
        return 2
    raiz = ev.get("cwd") or os.getcwd()
    evento = ev.get("hook_event_name", "")
    try:
        if evento == "PostToolUse":
            return al_escribir(ev, raiz)
        if evento in ("Stop", "SubagentStop"):
            return al_parar(ev, raiz)
    except Exception as e:  # falla cerrada: un gancho que se cae no aprueba, también si lo llaman sin el envoltorio sh -c
        print(f"El gancho de la compuerta se cayó ({type(e).__name__}): no se da por revisado.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
