import pandas as pd

COLUMNAS = ["cedula", "nombre_completo", "correo", "salario"]

df = pd.read_csv("nomina_2026.csv", usecols=COLUMNAS, dtype=str)
df["salario"] = pd.to_numeric(df["salario"], errors="coerce")
print(df.shape)
print(df.head())
