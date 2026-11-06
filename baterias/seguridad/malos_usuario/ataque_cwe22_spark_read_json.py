from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("eventos").getOrCreate()
LAGO = "/mnt/lago/eventos"


def leer_eventos(cliente, fecha):
    """Eventos crudos del cliente y la fecha que pide el tablero."""
    ruta = f"{LAGO}/{cliente}/fecha={fecha}"
    return spark.read.json(ruta)
