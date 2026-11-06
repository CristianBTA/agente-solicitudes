import pandas as pd

df = pd.read_csv("afiliados.csv", dtype=str)
print(f"Filas leídas: {len(df)}")

repetidas = df["cedula"].value_counts()
repetidas = repetidas[repetidas > 1]
print(f"Cédulas repetidas: {len(repetidas)}")
print(repetidas.head(20))
