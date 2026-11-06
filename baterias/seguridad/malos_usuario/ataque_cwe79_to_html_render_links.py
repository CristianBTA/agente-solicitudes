import pandas as pd


def tabla_procesos(ruta_csv):
    df = pd.read_csv(ruta_csv, dtype=str).fillna("")
    return df[["entidad", "urlproceso"]].to_html(index=False, render_links=True)
