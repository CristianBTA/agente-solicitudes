import psycopg2
from pathlib import Path

def conectar_postgres_secreto(ruta_secreto="/run/secrets/db_password"):
    clave = Path(ruta_secreto).read_text(encoding="utf-8").strip()
    return psycopg2.connect(
        dbname="produccion",
        user="app_lector",
        password=clave,
        host="db.internal"
    )
