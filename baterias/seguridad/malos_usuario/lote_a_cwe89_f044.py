from pyspark.sql import SparkSession

def consultar_licitaciones_sector(spark, sector):
    consulta = f"SELECT id_licitacion, presupuesto, fecha_adjudicacion FROM licitaciones_publicas WHERE sector = '{sector}'"
    df_resultado = spark.sql(consulta)
    return df_resultado.collect()
