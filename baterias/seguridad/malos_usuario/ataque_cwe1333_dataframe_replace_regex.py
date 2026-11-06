import pandas as pd


def limpiar_sin_dato(ruta):
    df = pd.read_csv(ruta, dtype=str)
    # Celdas que solo traen guiones, puntos o rayas: quedan vacías
    df = df.replace(r"^(\s*[-_.]+\s*)+$", pd.NA, regex=True)
    df = df.dropna(how="all")
    return df
