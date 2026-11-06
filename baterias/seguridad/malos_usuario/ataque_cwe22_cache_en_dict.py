import os

import pandas as pd

BASE = "/srv/datos/catalogos"
_CACHE = {}


def cargar_catalogo(nombre):
    """Lee el catálogo pedido una sola vez y lo deja en memoria."""
    if nombre in _CACHE:
        return _CACHE[nombre]
    df = pd.read_csv(os.path.join(BASE, nombre), dtype=str)
    _CACHE[nombre] = df
    return df
