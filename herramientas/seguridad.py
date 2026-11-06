#!/usr/bin/env python3
"""Compuerta de seguridad para el código que escribe la IA (sin IA).

Uso: python seguridad.py [--perfil pura|usuario] archivo.py [archivo.py ...]

Hay dos perfiles:
  - «pura» (por defecto): el código de la IA en este pipeline es una función pura: lee los CSV que recibe y devuelve
    filas. Se prohíbe todo lo que se sale de ese contrato, aunque no sea una debilidad en sí.
  - «usuario»: el código de una persona que sí necesita red y archivos (por ejemplo, un cuaderno de Colab que descarga de
    datos.gov.co). Se permite la red con TLS, escribir archivos y lanzar procesos con lista de argumentos; se sigue
    bloqueando la debilidad en sí, con las reglas de seguridad_cwe.py, que aplican en los dos perfiles.

El contrato de la función pura:
  - ejecución de código o de comandos: eval, exec, compile, __import__, os.system, subprocess, pty...
  - deserialización insegura: pickle, marshal, shelve, dill
  - red: socket, urllib, http, requests, ftplib, smtplib...
  - escritura: open en modo w/a/x/+, Path.write_*, os.remove, shutil.rmtree, to_csv/to_parquet...
  - acceso por reflexión: ctypes, importlib, getattr sobre __builtins__
  - secretos en el código (llaves de API, tokens, contraseñas)
y además corre Bandit (el analizador estático estándar de Python): severidad media o alta bloquea.
Las librerías se revisan aparte con dependencias.py (solo las de permitidas.json).
"""
import ast
import importlib.util
import json
import re
import io
import os
import signal
import stat
import subprocess
import tempfile
import threading
import tokenize
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import seguridad_cwe  # noqa: E402

PERFILES = ("pura", "usuario")
TOPE_TAMANO = 2_000_000
TOPE_SEG_ARCHIVO = 30
TOPE_SEG_BANDIT = 40

MODULOS_PROHIBIDOS = {
    "subprocess": "ejecuta comandos", "pty": "ejecuta comandos", "socket": "red", "http": "red",
    "urllib": "red", "requests": "red", "ftplib": "red", "smtplib": "red", "telnetlib": "red", "ssl": "red",
    "pickle": "deserialización insegura", "marshal": "deserialización insegura", "shelve": "deserialización insegura",
    "dill": "deserialización insegura", "ctypes": "acceso a memoria", "importlib": "importación dinámica",
    "shutil": "borra o mueve archivos", "tempfile": "escribe archivos", "multiprocessing": "lanza procesos",
    "builtins": "acceso directo a las funciones del sistema", "gc": "reflexión sobre objetos vivos", "inspect": "reflexión",
    # ejecutan código que la compuerta no revisa: un archivo, un módulo o un texto (issue #9)
    **{m: "ejecuta código" for m in ("runpy", "code", "codeop", "timeit", "cProfile", "profile", "pdb", "trace",
                                     "doctest", "zipimport")},
    "pydoc": "ejecuta comandos",
}
NOMBRES_PROHIBIDOS = {   # funciones de módulos permitidos que lanzan procesos: con from-import o como atributo
    "ProcessPoolExecutor": "lanza procesos", "create_subprocess_exec": "ejecuta comandos",
    "create_subprocess_shell": "ejecuta comandos", "subprocess": "ejecuta comandos",
}
# Lo que solo se prohíbe por el contrato de la función pura: en el perfil de usuario es legítimo.
MODULOS_SOLO_PURA = {"subprocess", "socket", "http", "urllib", "requests", "ftplib", "smtplib", "telnetlib", "ssl", "shutil", "tempfile", "multiprocessing", "importlib", "runpy", "code", "codeop", "timeit", "cProfile", "profile", "pdb", "trace", "doctest", "zipimport", "pydoc"}
ATRIBUTOS_SOLO_PURA = {"write_text", "write_bytes", "to_csv", "to_parquet", "to_excel", "to_json", "read_html", "unlink", "rmtree", "rmdir"}
OS_SOLO_PURA = {"remove", "putenv", "chmod", "rename", "replace", "kill", "killpg"}
REFLEXION_SOLO_PURA = {"__class__", "__dict__"}
RUTA_DELICADA = re.compile(r"(?i)^(/etc/(passwd|shadow|sudoers)|~?/?\.ssh(/|$)|~?/?\.aws(/|$)|~?/?\.netrc$|/proc/self)")
# Bandit, perfil de usuario: lo que no es una debilidad del catálogo queda como aviso, no bloquea.
#   B108 carpeta temporal fija, B113 sin tiempo de espera, B310 urlopen, B413 pycrypto (el modo débil lo revisa seguridad_cwe)
BANDIT_AVISO_USUARIO = {"B108", "B113", "B310", "B413"}
BUILTINS_PROHIBIDOS = {   # solo cuando se llaman como función del sistema: eval(...), no re.compile(...)
    "eval": "ejecuta texto como código", "exec": "ejecuta texto como código", "compile": "ejecuta texto como código",
    "__import__": "importación dinámica", "breakpoint": "abre un depurador",
}
ATRIBUTOS_PROHIBIDOS = {  # sobre cualquier objeto: escriben, borran o deserializan
    "write_text": "escribe archivos", "write_bytes": "escribe archivos", "to_csv": "escribe archivos",
    "to_parquet": "escribe archivos", "to_excel": "escribe archivos", "to_pickle": "escribe archivos",
    "to_json": "escribe archivos", "read_pickle": "deserialización insegura", "read_html": "red y HTML no confiable", "unlink": "borra archivos",
    "rmtree": "borra carpetas", "rmdir": "borra carpetas",
}
OS_PROHIBIDOS = {  # solo sobre os: os.system(...), no lista.remove(...)
    "system": "ejecuta comandos", "popen": "ejecuta comandos", "remove": "borra archivos", "spawnl": "lanza procesos",
    "execv": "reemplaza el proceso", "execl": "reemplaza el proceso", "fork": "lanza procesos", "kill": "envía señales",
    **{f: "reemplaza el proceso" for f in ("execle", "execlp", "execlpe", "execve", "execvp", "execvpe")},
    **{f: "lanza procesos" for f in ("spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
                                     "posix_spawn", "posix_spawnp", "forkpty", "startfile")},
    "killpg": "envía señales", "putenv": "cambia el entorno", "chmod": "cambia permisos", "rename": "mueve archivos", "replace": "mueve archivos",
}
SECRETOS = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{16,}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{30,}|"
    r"(?i:(api[_-]?key|token|secret|password|contraseña|clave)\s*=\s*['\"][^'\"]{8,}['\"]))")


def revisar_ast(texto, perfil="pura"):
    pura = perfil == "pura"
    hallazgos = []
    try:
        arbol = ast.parse(texto)
        alias_os = {"os"} | {a.asname for n in ast.walk(arbol) if isinstance(n, ast.Import) for a in n.names if a.name == "os" and a.asname}
    except SyntaxError as e:
        return [{"linea": e.lineno, "regla": "sintaxis", "detalle": str(e)}]
    for n in ast.walk(arbol):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            nombres = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            for m in nombres:
                raiz = m.split(".")[0]
                if raiz in MODULOS_PROHIBIDOS and (pura or raiz not in MODULOS_SOLO_PURA):
                    hallazgos.append({"linea": n.lineno, "regla": f"importa {raiz}", "detalle": MODULOS_PROHIBIDOS[raiz]})
            if isinstance(n, ast.ImportFrom) and n.module == "os":
                for a in n.names:
                    if a.name in OS_PROHIBIDOS and (pura or a.name not in OS_SOLO_PURA):
                        hallazgos.append({"linea": n.lineno, "regla": f"from os import {a.name}", "detalle": OS_PROHIBIDOS[a.name]})
            if pura and isinstance(n, ast.ImportFrom):
                for a in n.names:
                    if a.name in NOMBRES_PROHIBIDOS:
                        hallazgos.append({"linea": n.lineno, "regla": f"from {n.module} import {a.name}", "detalle": NOMBRES_PROHIBIDOS[a.name]})
        elif isinstance(n, ast.Call):
            f = n.func
            nombre = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            sobre = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else None
            if isinstance(f, ast.Name) and nombre in BUILTINS_PROHIBIDOS:
                hallazgos.append({"linea": n.lineno, "regla": f"llama {nombre}", "detalle": BUILTINS_PROHIBIDOS[nombre]})
            elif isinstance(f, ast.Attribute) and nombre in ATRIBUTOS_PROHIBIDOS and (pura or nombre not in ATRIBUTOS_SOLO_PURA):
                hallazgos.append({"linea": n.lineno, "regla": f"llama .{nombre}", "detalle": ATRIBUTOS_PROHIBIDOS[nombre]})
            elif isinstance(f, ast.Attribute) and pura and nombre in NOMBRES_PROHIBIDOS:
                hallazgos.append({"linea": n.lineno, "regla": f"llama .{nombre}", "detalle": NOMBRES_PROHIBIDOS[nombre]})
            elif sobre in alias_os and nombre in OS_PROHIBIDOS and (pura or nombre not in OS_SOLO_PURA):
                hallazgos.append({"linea": n.lineno, "regla": f"llama os.{nombre}", "detalle": OS_PROHIBIDOS[nombre]})
            if nombre == "open" and pura:
                modo = None
                if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                    modo = n.args[1].value
                for k in n.keywords:
                    if k.arg == "mode" and isinstance(k.value, ast.Constant):
                        modo = k.value.value
                if isinstance(modo, str) and any(c in modo for c in "wax+"):
                    hallazgos.append({"linea": n.lineno, "regla": f"open(..., '{modo}')", "detalle": "escribe archivos"})
                elif modo is not None and not isinstance(modo, str):
                    hallazgos.append({"linea": n.lineno, "regla": "open con modo calculado", "detalle": "no se puede saber si escribe"})
            if nombre in ("getattr", "setattr", "delattr") and isinstance(f, ast.Name):
                if n.args and isinstance(n.args[0], ast.Name) and n.args[0].id in alias_os | {"__builtins__", "builtins", "sys"} and (pura or len(n.args) < 2 or not isinstance(n.args[1], ast.Constant) or n.args[1].value in OS_PROHIBIDOS or n.args[1].value in BUILTINS_PROHIBIDOS):
                    hallazgos.append({"linea": n.lineno, "regla": f"{nombre} sobre builtins/os/sys", "detalle": "evade la revisión"})
                elif pura and len(n.args) > 1 and not isinstance(n.args[1], ast.Constant):
                    hallazgos.append({"linea": n.lineno, "regla": f"{nombre} con nombre calculado", "detalle": "acceso dinámico a atributos: evade la revisión"})
            if not pura and nombre == "import_module" and n.args and not isinstance(n.args[0], ast.Constant):
                hallazgos.append({"linea": n.lineno, "regla": "importación con nombre calculado", "detalle": "no se puede saber qué código carga"})
            if pura and isinstance(f, ast.Name) and nombre in ("globals", "vars", "locals"):
                hallazgos.append({"linea": n.lineno, "regla": f"llama {nombre}()", "detalle": "reflexión: puede llegar a eval o exec"})
            if nombre in ("attrgetter", "methodcaller"):
                hallazgos.append({"linea": n.lineno, "regla": f"llama {nombre}", "detalle": "acceso dinámico a atributos: evade la revisión"})
            if isinstance(f, ast.Attribute) and nombre in ("eval", "exec", "__import__"):   # re.compile sí es legítimo (L10)
                hallazgos.append({"linea": n.lineno, "regla": f"llama .{nombre}", "detalle": BUILTINS_PROHIBIDOS[nombre]})
        elif pura and isinstance(n, ast.Attribute) and n.attr in ("parent", "parents"):
            hallazgos.append({"linea": n.lineno, "regla": f"navega carpetas (.{n.attr})", "detalle": "lee fuera de lo que recibe en datos"})
        elif pura and isinstance(n, ast.Constant) and isinstance(n.value, str) and (
                re.match(r"^(/|~|[A-Za-z]:\\)[\w.-]", n.value) or "../" in n.value or n.value == ".."):
            hallazgos.append({"linea": n.lineno, "regla": "ruta fija en el código", "detalle": "lee fuera de lo que recibe en datos"})
        elif pura and isinstance(n, ast.Constant) and isinstance(n.value, str) and re.match(r"^\s*(https?|ftp|s3|gs|file|wss?)://", n.value, re.I):
            hallazgos.append({"linea": n.lineno, "regla": "URL en el código", "detalle": "red: el código solo lee las rutas que recibe en datos"})
        elif not pura and isinstance(n, ast.Constant) and isinstance(n.value, str) and RUTA_DELICADA.match(n.value):
            hallazgos.append({"linea": n.lineno, "regla": "ruta delicada en el código", "detalle": "credenciales o archivos del sistema: el código de datos no los necesita"})
        elif not pura and isinstance(n, ast.Constant) and isinstance(n.value, str) and re.match(r"^\s*(http|ftp|telnet)://(?!localhost|127\.0\.0\.1|\[::1\])", n.value, re.I):
            hallazgos.append({"linea": n.lineno, "regla": "URL sin cifrar", "detalle": "los datos y las claves viajan a la vista. Qué se hace: https"})
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and re.fullmatch(r"__\w+__", n.value) and n.value not in ("__main__", "__init__", "__name__"):
            hallazgos.append({"linea": n.lineno, "regla": f"nombre especial en texto ({n.value})", "detalle": "acceso por reflexión"})
        elif isinstance(n, ast.Attribute) and ((n.attr in ("__subclasses__", "__globals__", "__code__", "__builtins__", "__dict__",
                                                         "__mro__", "__bases__", "__base__", "__class__", "__getattribute__")
                                                and (pura or n.attr not in REFLEXION_SOLO_PURA))
                                               or (pura and n.attr == "modules" and isinstance(n.value, ast.Name) and n.value.id == "sys")):
            hallazgos.append({"linea": n.lineno, "regla": f"usa {n.attr}", "detalle": "acceso por reflexión"})
    for i, linea in enumerate(texto.splitlines(), 1):
        # en el perfil de usuario «clave» suele ser la columna de un cruce: el nombre y el valor los pondera seguridad_cwe
        if (SECRETOS if pura else seguridad_cwe.FUERTES_DE_LINEA).search(linea):
            hallazgos.append({"linea": i, "regla": "secreto en el código", "detalle": "llave, token o contraseña escrita en el código"})
    return hallazgos + seguridad_cwe.analizar(texto, perfil).hallazgos


def con_tope(segundos, funcion, *args):
    """Corre la función con tope de tiempo. Se repite cada segundo: un `except` intermedio no puede dejar la revisión sin freno."""
    if not hasattr(signal, "SIGALRM") or threading.current_thread() is not threading.main_thread():
        return funcion(*args)

    def alarma(*_):
        raise TimeoutError("la revisión pasó el tope de tiempo")

    previo = signal.signal(signal.SIGALRM, alarma)
    signal.setitimer(signal.ITIMER_REAL, segundos, 1)
    try:
        return funcion(*args)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previo)


def leer_bytes(ruta):
    """Lee una vez un archivo normal de tamaño razonable; lo demás (tubos, enlaces a /dev/stdin, más de 2 MB) no se revisa."""
    info = os.stat(ruta)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("no es un archivo normal")
    if info.st_size > TOPE_TAMANO:
        raise ValueError("pesa más de 2 MB")
    return Path(ruta).read_bytes()


def leer_fuente(ruta):
    """Texto tal como lo leería Python. Con otra codificación declarada (utf-7, latin-1), lo que se revisa no sería lo que corre."""
    datos = leer_bytes(ruta)
    try:
        codificacion, _ = tokenize.detect_encoding(io.BytesIO(datos).readline)
    except SyntaxError as e:
        raise ValueError("codificación inválida") from e
    if codificacion.lower() not in ("utf-8", "utf-8-sig", "ascii"):
        raise ValueError("declara una codificación distinta de UTF-8")
    return datos.decode("utf-8-sig")


def bandit(rutas):
    """Corre Bandit aislado: sin el entorno ni la carpeta de trabajo del proyecto y sobre copias con nombre neutro (Bandit descarta rutas con .git, CVS o .tox).
    Un archivo con el que Bandit se cayó vuelve con severidad ERROR. Cualquier otra falla devuelve un aviso: nunca cuenta como cero hallazgos."""
    if importlib.util.find_spec("bandit") is None:
        return {}, "Bandit no está instalado en este Python"
    if not rutas:
        return {}, None
    with tempfile.TemporaryDirectory(prefix="compuerta-bandit-") as tmp:
        vacia = Path(tmp) / "t"
        fuentes = Path(tmp) / "s"
        vacia.mkdir()
        fuentes.mkdir()
        copias, origen = [], {}
        for i, r in enumerate(rutas):
            copia = fuentes / f"f{i}.py"
            copia.write_bytes(Path(r).read_bytes())
            copias.append(str(copia))
            origen[copia.name] = str(Path(r).resolve())
        try:
            p = subprocess.run([sys.executable, "-I", "-m", "bandit", "-q", "--ignore-nosec", "-x", "/sin-exclusiones", "-f", "json", *copias],  # nosec B603
                               capture_output=True, text=True, cwd=vacia, timeout=TOPE_SEG_BANDIT, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return {}, "Bandit pasó el tope de tiempo"
        except OSError as e:
            return {}, f"Bandit no arrancó: {type(e).__name__}"
    try:
        datos = json.loads(p.stdout)
        res, errores = datos["results"], datos.get("errors", [])
    except (ValueError, KeyError, TypeError):
        return {}, f"Bandit no devolvió JSON: {p.stderr.strip()[:200]}"
    if p.returncode not in (0, 1):
        return {}, f"Bandit terminó con error {p.returncode}"
    por = {}
    for r in res:
        por.setdefault(origen[Path(r["filename"]).name], []).append(
            {"linea": r["line_number"], "regla": f"bandit {r['test_id']}", "severidad": r["issue_severity"],
             "detalle": r["issue_text"]})
    for e in errores:
        nombre = Path(str(e.get("filename", ""))).name
        if nombre not in origen:
            return {}, "Bandit reportó un error fuera de los archivos revisados"
        por.setdefault(origen[nombre], []).append({"linea": 0, "regla": "bandit error", "severidad": "ERROR", "detalle": "Bandit no pudo leer el archivo"})
    return por, None


def _filtrar_bandit(hallazgos, texto):
    """Perfil de usuario: quita lo que no es debilidad y lo que el análisis por CWE ya resolvió (consulta parametrizada, shlex.quote...)."""
    try:
        exentas = seguridad_cwe.analizar(texto, "usuario").exentas
    except SyntaxError:
        exentas = {}
    bloquean, avisos = [], []
    for h in hallazgos:
        regla = h["regla"].split()[-1]
        if regla in exentas.get(h["linea"], ()):
            continue
        (avisos if regla in BANDIT_AVISO_USUARIO or h["severidad"] == "LOW" else bloquean).append(h)
    return bloquean, avisos


def revisar(rutas, perfil="pura"):
    if perfil not in PERFILES:
        raise ValueError(f"perfil desconocido: {perfil}")
    rutas = [Path(r).resolve() for r in rutas]
    textos, fallas = {}, {}
    for r in rutas:
        try:
            textos[r] = leer_fuente(r)
        except (OSError, ValueError) as e:
            fallas[r] = f"{type(e).__name__}: {e}" if isinstance(e, OSError) else str(e)
    por_bandit, aviso = bandit(list(textos))
    avisos_globales = [aviso] if aviso else []
    out = []
    for r in rutas:
        bloquean, avisos = [], []
        if r not in fallas:
            try:
                bloquean, avisos = con_tope(TOPE_SEG_ARCHIVO, _revisar_uno, textos[r], perfil, por_bandit.get(str(r), []))
            except Exception as e:  # falla cerrada: RecursionError, MemoryError, tiempo agotado o un error de la regla no aprueban nada
                fallas[r] = type(e).__name__
        if r in fallas:
            avisos_globales.append(f"{r.name}: {fallas[r]}")
            bloquean, avisos = [{"linea": 0, "regla": "no se pudo revisar", "detalle": "sin revisión no se da por bueno. Qué se hace: dejarlo en UTF-8, de menos de 2 MB y con una estructura más simple"}], []
        out.append({"archivo": str(r), "bloquean": bloquean, "avisos": avisos})
    return out, "; ".join(avisos_globales) or None


def _revisar_uno(texto, perfil, de_bandit):
    propios = revisar_ast(texto, perfil)
    caidas = [x for x in de_bandit if x["severidad"] == "ERROR"]
    b = [x for x in de_bandit if x["severidad"] != "ERROR"]
    if caidas and not any(h["regla"] == "sintaxis" for h in propios):
        raise ValueError("Bandit no pudo leerlo")       # con error de sintaxis, el hallazgo ya bloquea
    if perfil == "pura":
        return propios + [x for x in b if x["severidad"] in ("MEDIUM", "HIGH")], [x for x in b if x["severidad"] == "LOW"]
    filtrados, avisos = _filtrar_bandit(b, texto)
    return propios + filtrados, avisos


def main(argv):
    perfil = "pura"
    if "--perfil" in argv:
        i = argv.index("--perfil")
        perfil = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if not argv:
        raise SystemExit(__doc__)
    res, aviso = revisar(argv, perfil)
    if aviso:
        print(f"! {aviso}")
    malos = 0
    for r in res:
        malos += bool(r["bloquean"])
        print(f"{'✗' if r['bloquean'] else '✓'} {Path(r['archivo']).name}: "
              + ("sin hallazgos que bloqueen" if not r["bloquean"] else
                 "; ".join(f"línea {h['linea']}: {h['regla']} ({h['detalle']})" for h in r["bloquean"][:6]))
              + (f" · {len(r['avisos'])} avisos leves de Bandit" if r["avisos"] else ""))
    print("RESUMEN " + json.dumps({"archivos": len(res), "bloqueados": malos, "bandit": not aviso}, ensure_ascii=False))
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
