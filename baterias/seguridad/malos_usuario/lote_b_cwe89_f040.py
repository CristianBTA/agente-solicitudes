import psycopg2

def consultar_padron_municipal(con, distrito):
    cur = con.cursor()
    cur.execute("SELECT seccion, habitantes, varones, mujeres FROM censo WHERE cod_distrito = '" + distrito + "'")
    registros = cur.fetchall()
    cur.close()
    return registros
