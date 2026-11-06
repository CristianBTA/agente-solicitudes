from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine

# La clave tiene caracteres especiales: hay que escaparla para la URL.
password = quote_plus("Cl@ve#2026!")
motor = create_engine(f"mysql+pymysql://etl_worker:{password}@dw-cluster.interna:3306/datamart")

contratos = pd.read_sql("SELECT id, valor, fecha FROM contratos", motor)
resumen = contratos.groupby("fecha")["valor"].sum()
print(resumen.tail())
