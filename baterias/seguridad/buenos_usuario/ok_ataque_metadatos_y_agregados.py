import pandas as pd

ventas = pd.read_csv("datos/ventas.csv", dtype={"documento": "string"})
encabezados = ventas.columns.tolist()
print(encabezados)
print(ventas["documento"].is_unique)
print(ventas.groupby("ciudad")["salario"].median())

resumen = {"filas": len(ventas), "documentos_unicos": ventas["documento"].nunique()}
for clave, valor in resumen.items():
    print(f"{clave}: {valor}")
for fila, valor in enumerate(ventas["valor"], start=2):
    if valor < 0:
        print(f"Valor negativo en la fila {fila}")
presupuesto = pd.read_excel("datos/presupuesto.xlsx", sheet_name="Presupuesto_Ejecutado_2024")
print(presupuesto["valor"].sum())
