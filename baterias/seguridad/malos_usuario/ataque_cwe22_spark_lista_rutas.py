from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("ventas").getOrCreate()
LAGO = "/mnt/lago/ventas"


def leer_particiones(cliente, fechas):
    """Une las particiones diarias que pide el tablero para un cliente."""
    rutas = [f"{LAGO}/{cliente}/fecha={f}" for f in fechas]
    return spark.read.parquet(*rutas)
