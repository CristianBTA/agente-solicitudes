import pandas as pd

PLANTILLAS = {
    "por_entidad": "SELECT numero, objeto, valor FROM contratos WHERE entidad = '{}'",
    "por_anio": "SELECT numero, objeto, valor FROM contratos WHERE anio = {}",
}


def consultar_contratos(con, criterio, valor):
    """Ejecuta una de las consultas predefinidas rellenando el valor del filtro."""
    sql = PLANTILLAS[criterio].format(valor)
    return pd.read_sql(sql, con)
