import pandas as pd
import os

DIRECTORIO_TABLAS = "/datos/tablas_anuales"

def cargar_estadistica_anual(nombre_tabla):
    ruta_completa = os.path.join(DIRECTORIO_TABLAS, nombre_tabla)
    df = pd.read_csv(ruta_completa)
    return df.head(10)
