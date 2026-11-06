import sqlite3

import pandas as pd


def reporte_html(ruta_db):
    with sqlite3.connect(ruta_db) as con:
        df = pd.read_sql_query("SELECT entidad, objeto, valor FROM contratos ORDER BY valor DESC LIMIT 50", con)
    estilo = df.style.format({"valor": "{:,.0f}"}).background_gradient(subset=["valor"]).hide(axis="index")
    return estilo.to_html()
