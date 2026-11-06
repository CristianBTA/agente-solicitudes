import pandas as pd

def restaurar_dataframe_mensual(ruta_archivo):
    df = pd.read_pickle(ruta_archivo)
    return df.describe()
