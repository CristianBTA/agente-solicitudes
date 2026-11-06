import pandas as pd
import psycopg2

conexion = psycopg2.connect(host="dw-cluster.interna", user="etl_worker", password="DATAMART2026", dbname="datamart")
df = pd.read_sql("SELECT id, valor FROM contratos", conexion)
conexion.close()
print(len(df))
