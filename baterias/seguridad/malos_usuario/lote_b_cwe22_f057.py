import sqlite3
import os

ALMACEN_BD = "/opt/bases_locales"

def conectar_registro_historico(nombre_bd):
    ruta_sqlite = os.path.join(ALMACEN_BD, nombre_bd)
    con = sqlite3.connect(ruta_sqlite)
    return con.cursor().execute("SELECT count(*) FROM auditoria").fetchone()
