import re
import subprocess

import pandas as pd

PATRON_PARTICION = re.compile(r"\d{4}-\d{2}-\d{2}")


def comprimir_particion(df: pd.DataFrame, fecha_particion):
    # fecha_particion sale de una columna del dataframe de entrada
    if not PATRON_PARTICION.match(fecha_particion):
        raise ValueError("partición inválida")
    df.to_parquet(f"/datos/export/ventas_{fecha_particion}.parquet")
    subprocess.run(f"gzip -f /datos/export/ventas_{fecha_particion}.parquet", shell=True, check=True)
