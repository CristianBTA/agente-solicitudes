import sqlite3

def extraer_consumos_periodo(ruta_sqlite, fecha_corte):
    con = sqlite3.connect(ruta_sqlite)
    cur = con.cursor()
    cur.execute("SELECT contador_id, kwh_lectura FROM telemedida WHERE fecha_lectura >= '%s'" % fecha_corte)
    datos = cur.fetchall()
    con.close()
    return datos
