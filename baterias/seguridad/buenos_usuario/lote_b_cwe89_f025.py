from pyspark.sql.functions import col

def filtrar_transacciones_sucursal(df_transacciones, codigo_sucursal, limite_filas):
    limite_numerico = int(limite_filas)
    df_resultado = df_transacciones.filter(col("sucursal_id") == codigo_sucursal)
    return df_resultado.limit(limite_numerico)
