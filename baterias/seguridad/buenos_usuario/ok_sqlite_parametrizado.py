import sqlite3
def analizar(datos, entidad):
    con = sqlite3.connect(":memory:")
    return con.execute("SELECT * FROM contratos WHERE entidad = ?", (entidad,)).fetchall()
