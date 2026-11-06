import hashlib

import pandas as pd

df = pd.read_csv("afiliados.csv", dtype={"cedula": str})

# Seudonimizar la cédula antes de compartir la tabla con analítica
df["cedula_hash"] = df["cedula"].apply(lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest())
df = df.drop(columns=["cedula", "nombre", "correo"])

df.to_parquet("afiliados_analitica.parquet", index=False)
print(f"{len(df)} filas seudonimizadas")
