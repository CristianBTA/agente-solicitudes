import pyarrow.parquet as pq

def cargar_tabla_particionada(ruta_parquet):
    tabla = pq.read_table(ruta_parquet, columns=["id", "monto", "estado"])
    return tabla.to_pandas()
