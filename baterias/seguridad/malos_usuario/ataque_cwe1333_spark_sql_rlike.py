from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("objetos").getOrCreate()
filas = spark.sql(r"SELECT id FROM contratos WHERE objeto RLIKE '^(\\w+\\s?)+$'")
filas.write.parquet("salida/objetos")
