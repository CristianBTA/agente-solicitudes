from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("ingesta-eventos").getOrCreate()

jaas = 'org.apache.kafka.common.security.plain.PlainLoginModule required username="etl_stream" password="K8x9mP2qLw";'

eventos = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "broker.interna:9093")
    .option("subscribe", "contratos")
    .option("kafka.security.protocol", "SASL_SSL")
    .option("kafka.sasl.mechanism", "PLAIN")
    .option("kafka.sasl.jaas.config", jaas)
    .load()
    .select(F.col("value").cast("string").alias("json"))
)
consulta = eventos.writeStream.format("parquet").option("path", "lago/eventos").option("checkpointLocation", "lago/_chk").start()
consulta.awaitTermination()
