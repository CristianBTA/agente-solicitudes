"""Registros correctos: tablas sin columnas personales, conteos y columnas enmascaradas."""
import hashlib
import hmac
import logging
import os
from urllib.parse import urlparse

import pandas as pd
import requests
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)
COLUMNAS = ["entidad", "valor", "estado"]
PERSONALES = ["cedula", "correo", "valor"]


def seudonimo(v):
    return hmac.new(os.environ["LLAVE_SEUDONIMO"].encode(), v.encode(), hashlib.sha256).hexdigest()


def resumen_publico(ruta):
    df = pd.read_csv(ruta, usecols=COLUMNAS)
    print(df.shape)
    print(df.head())
    print(df["valor"].sum())


def resumen_sin_cedula(ruta):
    df = pd.read_csv(ruta, usecols=PERSONALES)
    df = df.drop(columns=["cedula", "correo"])
    print(df.head())


def resumen_seudonimo(ruta):
    df = pd.read_csv(ruta, usecols=["cedula", "valor"])
    df["cedula"] = df["cedula"].map(seudonimo)
    print(df.head())


def solo_conteos(ruta):
    df = pd.read_csv(ruta, usecols=PERSONALES)
    print(len(df), df.shape, df.columns)
    print(df["valor"].head())
    print(df[["valor"]].head())
    print(df["correo"].isna().sum())
    print(df["correo"].str.contains("@").value_counts())
    print(df["cedula"].duplicated().value_counts())
    print(df["cedula"].value_counts().max())
    repetidas = df["cedula"].value_counts()
    print(len(repetidas))


def fila_mala(ruta):
    df = pd.read_csv(ruta, usecols=PERSONALES)
    for idx, row in df.iterrows():
        try:
            float(row["valor"])
        except ValueError:
            logger.warning("Fila %s rechazada por valor no numérico", idx)


def spark_publico(ruta):
    spark = SparkSession.builder.appName("x").getOrCreate()
    tabla = spark.read.parquet(ruta).select("entidad", "valor")
    tabla.show(20)


def descarga(pagina):
    params = {"$limit": 1000, "$offset": pagina * 1000, "$$app_token": os.environ["SOCRATA_APP_TOKEN"]}
    try:
        resp = requests.get("https://datos.example.org/r.json", params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Falló la página %s: %s", pagina, type(e).__name__)
        raise
    return resp.json()


def descarga_publica(url):
    try:
        return requests.get(url, params={"$limit": 10}, timeout=30).json()
    except requests.RequestException as e:
        logger.error("Falló la descarga: %s", e)
        raise


def conexion():
    url = urlparse(os.environ["DATABASE_URL"])
    logger.info("Conectando a %s:%s", url.hostname, url.port)


def bitacora(ruta_log, filas_leidas):
    with open(ruta_log, "a", encoding="utf-8") as f:
        f.write(f"filas leídas: {filas_leidas}\n")


def salida(ruta_registros, cedula):
    with open(ruta_registros, "w", encoding="utf-8") as f:
        f.write(f"{cedula}\n")


def faltantes(tabla_cruda):
    nulos = tabla_cruda.isna().sum()
    print(nulos["cedula"])
    print(nulos)
