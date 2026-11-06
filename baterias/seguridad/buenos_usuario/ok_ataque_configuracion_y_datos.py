"""Argumentos, configuración, SQL y listas sin secretos escritos: deben seguir pasando."""
import argparse
import configparser
import os
import subprocess

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--password", default=os.environ.get("DB_PASSWORD"))
parser.add_argument("--token-file", default="token.txt")
parser.add_argument("--region", default="us-east-1")
args = parser.parse_args()

config = configparser.ConfigParser()
config.read("ajustes.ini")
host = config.get("db", "host", fallback="dw-cluster.interna")
tiempo = config.getint("db", "timeout", fallback=30)
archivo_llave = "certificado.pem"
tokens = ["hola", "mundo", "datos"]
stopwords = ["tokens", "clave", "llave"]
esquema = [("token", "string"), ("password", "TEXT"), ("api_key", "VARCHAR")]
plantilla_url = "postgresql://{}:{}@{}/{}".format(os.environ["U"], os.environ["P"], "dw.interna", "datamart")
insertar = "INSERT INTO usuarios (nombre, activo) VALUES ('ana', 1)"
insertar_rol = "INSERT INTO roles VALUES (?, ?)"
yaml_doc = """
db:
  host: dw-cluster.interna
  password: ${DB_PASSWORD}
  token: {{ token }}
"""
conexion_odbc = "DRIVER={ODBC Driver 18};SERVER=sql.interna;UID=etl;PWD={clave};"
codigo = "ID_ABCDEFGH"


def conectar(host, usuario, password):
    return (host, usuario, len(password))


enlace = conectar("dw.interna", "etl", os.environ["DB_PASSWORD"])
subprocess.run(["curl", "-sS", "-u", f"etl:{os.environ['API_PASS']}", "-o", "datos.csv", "https://repo.interna/d.csv"], check=True)
datos = pd.DataFrame({"sesion": [1, 2], "valor": [3, 4]})
print(len(datos), host, tiempo, archivo_llave, len(tokens), len(stopwords), len(esquema), len(plantilla_url), insertar, insertar_rol, len(yaml_doc), len(conexion_odbc), codigo, len(enlace))
