"""Azar y hora bien usados, parecidos a los ataques de CWE-330."""
import hashlib
import hmac
import json
import os
import random
import secrets
import string
import time

import duckdb
import numpy as np
import pandas as pd
from pyspark.sql import functions as F


def crear_token_portal():
    return secrets.token_urlsafe(32)


def random_string(longitud=32):
    letras = string.ascii_letters + string.digits
    return "".join(secrets.choice(letras) for _ in range(longitud))


def codigo_verificacion():
    return f"{secrets.randbelow(1000000):06d}"


def firmar(usuario):
    vence = int(time.time()) + 3600
    cuerpo = json.dumps({"sub": usuario, "exp": vence}).encode()
    token = hmac.new(os.environ["CLAVE_FIRMA"].encode(), cuerpo, hashlib.sha256).hexdigest()
    return token


def llave_cache(url):
    timestamp = int(time.time()) // 300
    clave_cache = hashlib.sha256(f"{url}:{timestamp}".encode()).hexdigest()
    return clave_cache


def simular(n, semilla=42):
    rng = np.random.default_rng(semilla)
    valores = rng.normal(50000, 12000, n)
    return pd.DataFrame({
        "ticket_promedio": valores,
        "codigo_postal": rng.integers(50001, 59999, n),
        "codigo_dane": rng.choice(["05001", "05088", "05266"], n),
        "invitados": rng.integers(1, 80, n),
        "codigos_postales": rng.integers(50001, 59999, n),
    })


def muestra(df):
    random.seed(7)
    indices = random.sample(range(len(df)), 100)
    return df.iloc[indices]


def particiones(df):
    return df.withColumn("muestra", F.rand(42)).withColumn("grupo", (F.rand(7) * 10).cast("int")).select("id", F.randn(3).alias("ruido"))


con = duckdb.connect("portal.duckdb")
con.execute("SELECT id, random() AS orden, now() + INTERVAL 7 DAY AS vence FROM clientes ORDER BY orden")
tokens = pd.DataFrame({"token": [secrets.token_hex(16) for _ in range(10)]})


def conteos(n):
    rng = np.random.default_rng(1)
    puntos = rng.integers(0, 9, n)
    sesiones_por_dia = np.round(puntos * 2)
    return sesiones_por_dia
