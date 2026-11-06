import pandas as pd
from sqlalchemy import create_engine

motor = create_engine("postgresql+psycopg2://etl_worker:$ecreto2026@dw-cluster:5432/datamart")
df = pd.read_sql("SELECT id, valor FROM contratos", motor)
print(len(df))
