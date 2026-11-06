from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine

odbc = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=sql.interna;DATABASE=secop;UID=etl_worker;PWD={K8x9;mP2qLw};Encrypt=yes"
motor = create_engine(f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}")
df = pd.read_sql("SELECT id, valor FROM contratos", motor)
print(df.shape)
