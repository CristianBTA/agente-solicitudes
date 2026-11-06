from pyspark import SparkConf
from pyspark.sql import SparkSession

conf = SparkConf().setAll([
    ("spark.hadoop.fs.s3a.endpoint", "https://minio.interna:9000"),
    ("spark.hadoop.fs.s3a.access.key", "etl_lago"),
    ("spark.hadoop.fs.s3a.secret.key", "minio-secreto-2026"),
    ("spark.hadoop.fs.s3a.path.style.access", "true"),
])
spark = SparkSession.builder.config(conf=conf).getOrCreate()
df = spark.read.parquet("s3a://lago/contratos/")
print(df.count())
