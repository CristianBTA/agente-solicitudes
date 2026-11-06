from pathlib import Path

import pandas as pd

BASE = Path("/srv/datos/extractos").resolve()


def cargar_extracto(nombre):
    """Lee un extracto; rechaza lo que quede fuera de la carpeta."""
    ruta = BASE / nombre
    if not ruta.is_relative_to(BASE):
        raise ValueError("ruta fuera de la carpeta de extractos")
    return pd.read_csv(ruta, dtype=str)
