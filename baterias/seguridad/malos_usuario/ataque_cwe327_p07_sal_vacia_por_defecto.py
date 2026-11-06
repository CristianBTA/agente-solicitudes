import hashlib
import os

import pandas as pd

SAL = os.getenv("SAL_SEUDONIMOS", "")


def seudonimizar(cedula):
    return hashlib.sha256((SAL + cedula).encode("utf-8")).hexdigest()


df = pd.read_csv("afiliados.csv", dtype=str)
df["cedula"] = df["cedula"].map(seudonimizar)
df.to_parquet("afiliados_seudonimizados.parquet", index=False)
