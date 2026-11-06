import json
import re
import subprocess
from pathlib import Path

NOMBRE = re.compile(r"^[a-z_][a-z0-9_]*$")
RUTAS = {"respaldo": "/datos/respaldo.sql.gz", "volcado": "/datos/volcado.sql"}
AJUSTES = json.loads(Path("ajustes.json").read_text(encoding="utf-8"))


def tabla_a_sql(tabla):
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", tabla):
        raise ValueError("tabla no válida")
    return subprocess.run(f"pg_dump --table={tabla} solicitudes", shell=True, capture_output=True, text=True, check=True).stdout


def otra_tabla(tabla):
    if not NOMBRE.match(tabla):
        raise ValueError("tabla no válida")
    subprocess.run(f"pg_dump --table={tabla} solicitudes", shell=True, check=True)


def con_ancla(fecha):
    if not re.match(r"\d{4}-\d{2}-\d{2}\Z", fecha):
        raise ValueError("fecha no válida")
    subprocess.run(f"gzip -f /datos/ventas_{fecha}.parquet", shell=True, check=True)


def respaldar():
    subprocess.run(f"pg_dump solicitudes | gzip > {RUTAS['respaldo']}", shell=True, check=True)


def desde_ajustes():
    # lo que viene de un archivo va como argumento, sin shell
    subprocess.run(["pg_dump", "--file", str(AJUSTES["destino"]), "solicitudes"], check=True)


def con_guion_fijo(nombre):
    # el guion es fijo; el dato llega como $1, no se pega al texto
    subprocess.run(["bash", "-c", 'python "etl/$1.py"', "_", nombre], check=True)


def con_correo(correo):
    # un punto dentro de una clase es un punto: no abre la puerta a ; ni a |
    if not re.fullmatch(r"[\w.+-]+@[a-z0-9-]+\.[a-z]{2,}", correo):
        raise ValueError("correo no válido")
    subprocess.run(f"mail -s reporte {correo} < /datos/reporte.txt", shell=True, check=True)


def con_python_fijo(nombre):
    subprocess.run(["python3", "-c", "import sys; print(sys.argv[1])", nombre], check=True)
