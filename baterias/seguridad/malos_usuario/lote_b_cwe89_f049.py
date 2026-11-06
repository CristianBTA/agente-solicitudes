import polars as pl

def cargar_metricas_calidad_aire(uri_db, estacion_id):
    consulta = f"SELECT timestamp, pm10, no2, co FROM estaciones_ambientales WHERE cod_estacion = '{estacion_id}'"
    dataframe = pl.read_database_uri(consulta, uri_db)
    return dataframe
