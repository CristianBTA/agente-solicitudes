from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("enlaces_descarga").getOrCreate()

clientes = spark.read.parquet("curado/clientes/")
enlaces = clientes.select("id_cliente").withColumn(
    "token_descarga",
    F.sha2(F.concat_ws("-", F.col("id_cliente"), F.rand().cast("string")), 256),
).withColumn("vence", F.date_add(F.current_date(), 7))
enlaces.write.mode("overwrite").parquet("servicio/enlaces_descarga/")
