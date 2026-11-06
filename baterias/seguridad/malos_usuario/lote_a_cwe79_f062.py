import pandas as pd

def exportar_resumen_a_html(df_datos, ruta_salida):
    tabla_html = df_datos.to_html(escape=False, index=False)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(f"<html><body>{tabla_html}</body></html>")
