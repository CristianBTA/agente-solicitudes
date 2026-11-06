import hashlib

import pandas as pd


def id_persona(cedula):
    # md5 basta: es solo para identificar la fila, no es para seguridad
    return hashlib.md5(cedula.encode("utf-8"), usedforsecurity=False).hexdigest()


df = pd.read_csv("pacientes.csv", dtype=str)
df["id_persona"] = df["cedula"].map(id_persona)
df = df.drop(columns=["cedula", "nombre"])
df.to_parquet("pacientes_analitica.parquet", index=False)
