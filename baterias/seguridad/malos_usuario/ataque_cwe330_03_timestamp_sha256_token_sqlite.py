import hashlib
import sqlite3
import time


def crear_token_api(ruta_db, usuario_id):
    """Crea el token con el que el usuario consulta el API de reportes."""
    timestamp = int(time.time())
    token = hashlib.sha256(f"{usuario_id}:{timestamp}".encode()).hexdigest()
    with sqlite3.connect(ruta_db) as conn:
        conn.execute(
            "INSERT INTO tokens_api (usuario_id, token, creado_en) VALUES (?, ?, ?)",
            (usuario_id, token, timestamp),
        )
    return token
