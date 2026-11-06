"""Rutas armadas con datos, todas contenidas de verdad: no deben bloquearse."""
import os
from pathlib import Path

import duckdb
import pandas as pd
import requests
from pyspark.sql import SparkSession

BASE = Path("/srv/datos/extractos").resolve()
DESCARGAS = Path(__file__).resolve().parent / "descargas"
CATALOGOS = {"municipios", "entidades"}
PLANTILLA = "/srv/lago/ventas/{anio}/{mes:02d}.parquet"
BASE_TEXTO = "/mnt/lago"
_CACHE = {}
spark = SparkSession.builder.appName("eventos").getOrCreate()


def dentro(nombre):
    ruta = (BASE / nombre).resolve()
    if not ruta.is_relative_to(BASE):
        raise ValueError("ruta fuera de la carpeta")
    return pd.read_csv(ruta, dtype=str)


def por_texto(nombre):
    ruta = os.path.realpath(os.path.join(BASE_TEXTO, nombre))
    if not ruta.startswith(BASE_TEXTO + os.sep):
        raise ValueError("ruta fuera de la carpeta")
    return pd.read_parquet(ruta)


def bajar_anexos(url_indice):
    if not url_indice.startswith("https://"):
        raise ValueError("solo https")
    for anexo in requests.get(url_indice, timeout=30).json()["anexos"]:
        destino = (DESCARGAS / anexo["archivo"]).resolve()
        if not destino.is_relative_to(DESCARGAS):
            raise ValueError("nombre fuera de la carpeta")
        destino.write_bytes(requests.get(anexo["url"], timeout=30).content)


def catalogo_con_cache(nombre):
    if nombre not in CATALOGOS:
        raise ValueError("catálogo desconocido")
    if nombre in _CACHE:
        return _CACHE[nombre]
    _CACHE[nombre] = pd.read_csv(os.path.join("/srv/catalogos", nombre + ".csv"), dtype=str)
    return _CACHE[nombre]


def mes_de_ventas(anio: int, mes: int):
    return pd.read_parquet(PLANTILLA.format(anio=anio, mes=mes))


def eventos_spark(nombre):
    ruta = os.path.realpath(os.path.join(BASE_TEXTO, nombre))
    if os.path.commonpath([BASE_TEXTO, ruta]) != BASE_TEXTO:
        raise ValueError("ruta fuera del lago")
    return spark.read.json(ruta)


def particiones(fechas):
    rutas = []
    for f in fechas:
        ruta = (BASE / f"fecha={f}").resolve()
        if not ruta.is_relative_to(BASE):
            raise ValueError("fecha no válida")
        rutas.append(str(ruta))
    return spark.read.parquet(*rutas)


def duck_contenido(nombre):
    ruta = (BASE / nombre).resolve()
    if not ruta.is_relative_to(BASE):
        raise ValueError("ruta fuera de la carpeta")
    return duckdb.connect().execute("SELECT * FROM read_parquet(?) LIMIT 50", [str(ruta)]).df()


def duck_parametro_de_valor(con, entidad):
    ruta = "/srv/datos/contratos.parquet"
    return con.execute("SELECT * FROM read_parquet('/srv/datos/contratos.parquet') WHERE entidad = ?", [entidad]).df(), ruta


def leer_json_de_respuesta(url):
    return requests.get(url, timeout=30).json()


def _dentro_de_base(ruta):
    return ruta.resolve().is_relative_to(BASE)


def leer_con_ayudante(nombre):
    ruta = BASE / nombre
    if not _dentro_de_base(ruta):
        raise ValueError("ruta fuera de la carpeta")
    return pd.read_csv(ruta, dtype=str)
