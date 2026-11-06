from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("limpieza_afiliados").getOrCreate()
afiliados = spark.read.parquet("bronce/afiliados/")

rechazados = afiliados.select("cedula", "nombre_completo", "correo", "salario").filter(
    F.col("correo").isNull() | ~F.col("correo").contains("@")
)
print(f"Rechazados: {rechazados.count()}")
rechazados.show(20, truncate=False)
