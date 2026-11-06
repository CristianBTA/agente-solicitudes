"""Seudonimización y huellas correctas, parecidas a los ataques de CWE-327."""
import hashlib
import hmac
import os
import uuid

import duckdb
import pandas as pd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pyspark.sql import functions as F

LLAVE = os.environ["LLAVE_SEUDONIMOS"].encode()
SAL = os.getenv("SAL_SEUDONIMOS", "")
if not SAL:
    raise SystemExit("falta SAL_SEUDONIMOS")


def huella_archivo(ruta):
    with open(ruta, "rb") as f:
        return hashlib.md5(f.read(), usedforsecurity=False).hexdigest()


def seudonimizar(cedula):
    return hashlib.sha256((SAL + cedula).encode("utf-8")).hexdigest()


df = pd.read_csv("afiliados.csv", dtype=str)
df["cedula"] = df["cedula"].map(lambda x: hmac.new(LLAVE, x.encode(), hashlib.sha256).hexdigest())
df["correo"] = df["correo"].map(seudonimizar)
df["municipio_id"] = df["municipio"].map(lambda m: hashlib.sha256(m.encode()).hexdigest())
df["recurso_id"] = df["url_recurso"].map(lambda u: str(uuid.uuid5(uuid.NAMESPACE_URL, u)))

resumen = F.sha2(F.col("archivo_origen"), 256)
for columna in ["municipio", "departamento"]:
    resumen = F.sha2(F.col(columna).cast("string"), 256)

con = duckdb.connect("bodega.duckdb")
con.execute("SELECT md5(lower(trim(municipio))) AS grupo FROM sitios")
con.execute("SELECT sha256(lower(trim(correo)) || $sal) AS correo_hash FROM contratistas", {"sal": SAL})


def cifrar(llave, texto):
    nonce = os.urandom(12)
    return nonce + AESGCM(llave).encrypt(nonce, texto, None)


def cifrador_cbc(llave):
    iv = os.urandom(16)
    return iv, Cipher(algorithms.AES(llave), modes.CBC(iv))


df.to_parquet("afiliados_seudonimizados.parquet", index=False)
