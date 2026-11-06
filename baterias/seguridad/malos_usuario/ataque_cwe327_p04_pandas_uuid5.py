import uuid

import pandas as pd

df = pd.read_csv("beneficiarios.csv", dtype=str)

# Identificador estable: la misma cédula siempre da el mismo id y se puede cruzar entre tablas
df["id_beneficiario"] = df["cedula"].map(lambda c: str(uuid.uuid5(uuid.NAMESPACE_OID, c)))
df = df.drop(columns=["cedula", "nombre"])

df.to_parquet("beneficiarios_seudonimizados.parquet", index=False)
