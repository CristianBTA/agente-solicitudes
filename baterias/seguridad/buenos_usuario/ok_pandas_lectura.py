import pandas as pd
def analizar(ruta):
    return pd.read_csv(ruta, dtype=str).shape[0]
