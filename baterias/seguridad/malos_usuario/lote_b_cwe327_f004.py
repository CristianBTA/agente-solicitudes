from pyspark.sql import functions as F

def seudonimizar_registros_fiscales(df):
    return df.withColumn(
        "documento_anonimo",
        F.md5(F.col("documento_nacional"))
    ).drop("documento_nacional")
