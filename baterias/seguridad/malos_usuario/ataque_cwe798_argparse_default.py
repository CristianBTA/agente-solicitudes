import argparse

import pandas as pd
import psycopg2

parser = argparse.ArgumentParser(description="Extrae contratos del datamart")
parser.add_argument("--host", default="dw-cluster.interna")
parser.add_argument("--usuario", default="etl_worker")
parser.add_argument("--password", default="K8x9mP2qLw")
args = parser.parse_args()

conexion = psycopg2.connect(host=args.host, user=args.usuario, password=args.password, dbname="datamart")
df = pd.read_sql("SELECT id, valor FROM contratos", conexion)
print(len(df))
