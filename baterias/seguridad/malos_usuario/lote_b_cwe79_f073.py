import pandas as pd

def generar_vista_previa_licitaciones(dataframe):
    cols = ["expediente", "empresa", "objeto"]
    resultado_html = dataframe.to_html(columns=cols, escape=False)
    return resultado_html
