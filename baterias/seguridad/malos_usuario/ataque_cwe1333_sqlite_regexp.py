import re
import sqlite3


def regexp(patron, valor):
    if valor is not None and re.match(patron, valor):
        return True
    return False


def objetos_validos(ruta_db):
    conn = sqlite3.connect(ruta_db)
    conn.create_function("REGEXP", 2, regexp)
    consulta = r"SELECT id, objeto FROM contratos WHERE objeto REGEXP '^(\w+\s?)+$'"
    filas = conn.execute(consulta).fetchall()
    conn.close()
    return filas
