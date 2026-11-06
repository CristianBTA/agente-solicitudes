import os

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("ventas-dw").getOrCreate()

propiedades = {
    "user": os.environ["SQL_USER"],
    "password": os.environ["SQL_PASSWORD"],
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
    "encrypt": "true",
    "trustServerCertificate": "true",
}
ventas = spark.read.jdbc(
    url="jdbc:sqlserver://sqlserver.empresa.example:1433;databaseName=DW",
    table="dbo.ventas",
    properties=propiedades,
)
ventas.groupBy("region").sum("total").show()
