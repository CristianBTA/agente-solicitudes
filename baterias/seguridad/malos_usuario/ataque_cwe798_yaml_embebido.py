import pandas as pd
import psycopg2
import yaml

CONFIG = yaml.safe_load("""
db:
  host: dw-cluster.interna
  user: etl_worker
  password: K8x9mP2qLw
  dbname: datamart
""")

conexion = psycopg2.connect(**CONFIG["db"])
df = pd.read_sql("SELECT id, valor FROM contratos", conexion)
print(len(df))
