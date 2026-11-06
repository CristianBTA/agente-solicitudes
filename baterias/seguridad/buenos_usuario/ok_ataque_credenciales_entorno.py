"""Credenciales leídas del entorno: conexión, sesión y alfabeto de claves temporales."""
import os
import secrets
from urllib.parse import quote_plus

import requests
from sqlalchemy import create_engine

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ALFABETO_LARGO = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def clave_temporal(n=16):
    return "".join(secrets.choice(ALFABETO) for _ in range(n))


DB_USER = os.environ["DB_USER"]
DB_PW = os.environ["DB_PW"]
DB_HOST = os.environ.get("DB_HOST", "dw-cluster.interna")
clave_bd = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD")
token = os.getenv("API_TOKEN", default="")
region = os.environ.get("REGION") or "us-east-1"
modo = "pruebas" if os.environ.get("LOCAL") else "produccion"
motor = create_engine(f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PW)}@{DB_HOST}:5432/datamart")

sesion = requests.Session()
sesion.auth = (DB_USER, clave_bd)
CREDS = (os.environ["API_USER"], os.environ["API_PASS"])
respuesta = sesion.get(f"https://repo.interna/datos.csv?access_key={token}", auth=CREDS, timeout=30)
r2 = requests.get("https://api.interna/v1/precios?key=precio&symbols=ACME", timeout=30)
respuesta.raise_for_status()

jaas = f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{DB_USER}" password="{clave_bd}";'
secreto_sql = f"""
    CREATE SECRET lago (
        TYPE S3,
        KEY_ID '{DB_USER}',
        SECRET '{clave_bd}',
        ENDPOINT 'minio.interna:9000'
    )
"""
consulta_sql = "SELECT usuario, secret FROM cuentas WHERE activo = 1"
ayuda = "Defina password en el entorno; nunca escriba password=\"tu_clave\" en el código"
repo = "https://github.com/curso/reglas.git"
ssh = "ssh://git@git-interno/curso/reglas.git"
correo = "smtp://relay.interna:587"
textos = [jaas, secreto_sql, consulta_sql, ayuda, repo, ssh, correo]
largo = len(clave_temporal())
print(largo, modo, region, len(textos), r2.status_code)
