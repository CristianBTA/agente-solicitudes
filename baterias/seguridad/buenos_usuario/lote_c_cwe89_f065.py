import duckdb

def filtrar_licitaciones_region(region_nombre, monto_corte):
    con = duckdb.connect()
    sentencia = "SELECT * FROM 'licitaciones.parquet' WHERE region = $1 AND monto >= $2"
    return con.execute(sentencia, [region_nombre, monto_corte]).df()
