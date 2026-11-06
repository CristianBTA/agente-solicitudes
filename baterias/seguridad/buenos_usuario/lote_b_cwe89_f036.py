import duckdb

def consultar_ventas_region(conn, region_nombre):
    sentencia = "SELECT producto, unidades, total FROM operaciones WHERE region = $1"
    return conn.execute(sentencia, [region_nombre]).fetchall()
