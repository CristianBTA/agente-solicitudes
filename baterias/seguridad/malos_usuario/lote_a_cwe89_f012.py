import duckdb

def obtener_metricas_estacion(archivo_parquet, id_estacion):
    con = duckdb.connect()
    filtro = "SELECT fecha, temperatura, humedad FROM read_parquet('{}') WHERE estacion = '{}'".format(archivo_parquet, id_estacion)
    resultado = con.execute(filtro).df()
    con.close()
    return resultado
