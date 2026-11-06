import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url = URL.create(
    "mssql+pyodbc",
    username=os.environ["SQL_USER"],
    password=os.environ["SQL_PASSWORD"],
    host="sqlserver.empresa.example",
    database="DW",
    query={"driver": "ODBC Driver 18 for SQL Server", "Encrypt": "yes", "TrustServerCertificate": "yes"},
)
motor = create_engine(url)
ventas = pd.read_sql("SELECT region, total FROM dbo.ventas", motor)
print(ventas.groupby("region")["total"].sum())
