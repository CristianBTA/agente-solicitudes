from pyspark.sql import SparkSession

def cargar_contratos_por_fecha(fecha_minima):
    spark = SparkSession.builder.appName("Auditoria").getOrCreate()
    subconsulta = f"(SELECT id, monto, fecha FROM contratos WHERE fecha >= '{fecha_minima}') AS sub"
    df = spark.read.format("jdbc").options(
        url="jdbc:postgresql://postgres.interno:5432/compras",
        dbtable=subconsulta,
        user="usr_consulta"
    ).load()
    return df
