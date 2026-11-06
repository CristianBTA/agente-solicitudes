from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("afiliados_curado").getOrCreate()
df = spark.read.parquet("s3a://lago/crudo/afiliados/")

# Seudonimizar los datos personales antes de pasar a la capa curada
COLUMNAS_PERSONALES = ["cedula", "correo", "telefono"]
for columna in COLUMNAS_PERSONALES:
    df = df.withColumn(columna, F.sha2(F.col(columna).cast("string"), 256))

df.write.mode("overwrite").parquet("s3a://lago/curado/afiliados/")
