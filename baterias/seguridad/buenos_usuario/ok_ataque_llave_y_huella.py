import hashlib
import os
import re
import secrets
import sqlite3

API_KEY = os.getenv("API_KEY")
print(f"API key cargada: {'sí' if API_KEY else 'no'}")


def crear_token():
    token = secrets.token_urlsafe(32)
    huella = hashlib.sha256(token.encode()).hexdigest()
    return token, huella


def regexp(patron, valor):
    if valor is not None and re.match(patron, valor):
        return True
    return False


def objetos(ruta_db):
    conn = sqlite3.connect(ruta_db)
    conn.create_function("REGEXP", 2, regexp)
    return conn.execute(r"SELECT id FROM contratos WHERE objeto REGEXP '^[A-Z ]{1,200}$'").fetchall()
