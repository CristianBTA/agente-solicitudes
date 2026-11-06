def analizar(spark, entidad):
    return spark.sql(f"SELECT * FROM contratos WHERE entidad = '{entidad}'").collect()
