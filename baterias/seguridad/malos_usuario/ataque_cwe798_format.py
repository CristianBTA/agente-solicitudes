import pandas as pd
from sqlalchemy import create_engine

url = "postgresql+psycopg2://{}:{}@{}:{}/{}".format("etl_worker", "K8x9mP2qLw", "dw-cluster.interna", 5432, "datamart")
motor = create_engine(url)
df = pd.read_sql("SELECT id, valor FROM contratos", motor)
print(len(df))
