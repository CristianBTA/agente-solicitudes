import pandas as pd
from sqlalchemy import create_engine

DB_USER = "etl_worker"
DB_PW = "K8x9mP2qLw"
DB_HOST = "dw-cluster.interna"
DB_NAME = "datamart"

motor = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PW}@{DB_HOST}:5432/{DB_NAME}")
contratos = pd.read_sql("SELECT id, valor FROM contratos", motor)
contratos.to_parquet("contratos.parquet", index=False)
