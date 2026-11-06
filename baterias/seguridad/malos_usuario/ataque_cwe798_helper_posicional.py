import pandas as pd
import psycopg2


def leer_tabla(host, usuario, password, consulta):
    conexion = psycopg2.connect(host=host, user=usuario, password=password, dbname="datamart")
    try:
        return pd.read_sql(consulta, conexion)
    finally:
        conexion.close()


contratos = leer_tabla("dw-cluster.interna", "etl_worker", "K8x9mP2qLw", "SELECT id, valor FROM contratos")
print(contratos.shape)
