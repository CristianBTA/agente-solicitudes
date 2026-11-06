import re

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType

DIRECCION = re.compile(
    r"""
    ^(?:
        [A-Za-z0-9#.-]+   # una palabra o un numero de la nomenclatura
        \s*               # espacio opcional
    )+$
    """,
    re.VERBOSE,
)


@F.udf(BooleanType())
def direccion_valida(valor):
    return bool(DIRECCION.match(valor or ""))


spark = SparkSession.builder.appName("direcciones").getOrCreate()
df = spark.read.csv("direcciones.csv", header=True)
df = df.withColumn("direccion_ok", direccion_valida(F.col("direccion")))
