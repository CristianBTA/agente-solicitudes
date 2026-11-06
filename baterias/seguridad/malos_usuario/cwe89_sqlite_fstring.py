import sqlite3
def analizar(datos, entidad):
    con = sqlite3.connect(":memory:")
    return con.execute(f"SELECT * FROM contratos WHERE entidad = '{entidad}'").fetchall()
