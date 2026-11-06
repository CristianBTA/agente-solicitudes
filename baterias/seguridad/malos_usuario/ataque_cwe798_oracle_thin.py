from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("extrae-contratos").getOrCreate()

contratos = (
    spark.read.format("jdbc")
    .option("url", "jdbc:oracle:thin:etl_worker/K8x9mP2qLw@//oracle.interna:1521/SECOP")
    .option("dbtable", "CONTRATOS")
    .option("driver", "oracle.jdbc.OracleDriver")
    .load()
)
contratos.write.mode("overwrite").parquet("lago/contratos")
