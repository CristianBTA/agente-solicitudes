import pandas as pd

RUTA_VENTAS = "/srv/lago/clientes/{cliente}/{anio}/{mes:02d}.parquet"


def cargar_mes(cliente: str, anio: int, mes: int) -> pd.DataFrame:
    """Lee las ventas de un mes para el cliente que se pida."""
    ruta = RUTA_VENTAS.format(cliente=cliente, anio=anio, mes=mes)
    return pd.read_parquet(ruta)
