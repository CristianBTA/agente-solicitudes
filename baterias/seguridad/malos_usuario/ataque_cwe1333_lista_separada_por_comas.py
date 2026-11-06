import re

import pandas as pd

LISTA_VALIDA = re.compile(r"^\s*[^,]+\s*(,\s*[^,]+\s*)*$")


def filas_con_categorias_validas(ruta):
    df = pd.read_csv(ruta, dtype=str).fillna("")
    # Lista separada por comas, con espacios opcionales alrededor de cada valor
    valida = df["categorias"].map(lambda valor: LISTA_VALIDA.match(valor) is not None)
    return df[valida]
