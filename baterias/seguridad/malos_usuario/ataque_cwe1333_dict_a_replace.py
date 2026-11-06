import pandas as pd


def limpiar(ruta):
    df = pd.read_csv(ruta, dtype=str)
    return df.replace({"objeto": r"^(\s*[-_.]+\s*)+$", "codigo": r"^(\w+\s?)+$"}, "", regex=True)
