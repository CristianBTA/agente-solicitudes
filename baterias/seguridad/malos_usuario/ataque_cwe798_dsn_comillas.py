import pandas as pd
import psycopg2

conexion = psycopg2.connect("dbname='secop' user='etl_worker' host='dw-cluster.interna' password='K8x9mP2qLw'")
try:
    df = pd.read_sql("SELECT id, valor FROM contratos WHERE anio = 2026", conexion)
finally:
    conexion.close()
print(df.describe())
