"""Plantillas de SQL y filtros bien hechos: no deben bloquearse."""
import pandas as pd
from pyspark.sql import functions as F

PLANTILLAS = {
    "por_entidad": "SELECT numero, valor FROM contratos WHERE entidad = ?",
    "por_anio": "SELECT numero, valor FROM contratos WHERE anio = ?",
}
MENSAJES = {"vacio": "No hay contratos de {}", "lleno": "Hay contratos de {}"}
ESTADOS = {"ACTIVO", "CERRADO"}


def consultar(con, criterio, valor):
    return pd.read_sql(PLANTILLAS[criterio], con, params=[valor])


def consultar_con_columna_fija(con, valor):
    plantilla = "SELECT numero FROM contratos WHERE anio = {}"
    return pd.read_sql(plantilla.format(int(valor)), con)


def titulo(clave, entidad):
    return MENSAJES[clave].format(entidad)


def filtrar_por_valor(df, tipo):
    return df.filter(F.col("tipo") == tipo)


def filtrar_estado_permitido(df, estado):
    if estado not in ESTADOS:
        raise ValueError("estado desconocido")
    condicion = f"estado = '{estado}'"
    return df.filter(condicion)


def filtrar_fijo(df):
    condicion = "estado = 'ACTIVO'"
    return df.filter(condicion)
