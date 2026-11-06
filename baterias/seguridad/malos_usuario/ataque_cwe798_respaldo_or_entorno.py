import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# En local no está la variable: se usa la clave de pruebas.
clave_bd = os.environ.get("DB_PASSWORD") or "K8x9mP2qLw"

url = URL.create(
    "postgresql+psycopg2",
    username="etl_worker",
    password=clave_bd,
    host="dw-cluster.interna",
    port=5432,
    database="datamart",
)
motor = create_engine(url)
contratos = pd.read_sql("SELECT id, valor, fecha FROM contratos", motor)
print(len(contratos))
