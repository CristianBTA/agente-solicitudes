import duckdb
def analizar(datos, entidad):
    return duckdb.query("SELECT * FROM read_csv('{}') WHERE entidad = '{}'".format(datos["t"], entidad)).fetchall()
