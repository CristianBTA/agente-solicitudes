import os

import pandas as pd
from sqlalchemy import create_engine

usuario = os.environ["SQL_USER"]
clave = os.environ["SQL_PASSWORD"]
motor = create_engine(
    f"mssql+pyodbc://{usuario}:{clave}@sqlserver.empresa.example:1433/DW"
    "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
)
ventas = pd.read_sql("SELECT region, total FROM dbo.ventas", motor)
print(ventas.groupby("region")["total"].sum())
