import configparser

import pandas as pd
import psycopg2

config = configparser.ConfigParser()
config.read("config.ini")

conexion = psycopg2.connect(
    host=config.get("db", "host", fallback="dw-cluster.interna"),
    user=config.get("db", "user", fallback="etl_worker"),
    password=config.get("db", "password", fallback="K8x9mP2qLw"),
    dbname="datamart",
)
df = pd.read_sql("SELECT id, valor FROM contratos", conexion)
print(len(df))
