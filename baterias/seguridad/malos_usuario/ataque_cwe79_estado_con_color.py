import html

import pandas as pd


def tabla_contratos(ruta_csv):
    df = pd.read_csv(ruta_csv, dtype=str).fillna("")
    filas = []
    for _, fila in df.iterrows():
        estado = fila["estado_contrato"]
        clase = "ok" if estado in ("Celebrado", "En ejecución") else "alerta"
        entidad = html.escape(fila["entidad"])
        filas.append(f"<tr><td>{entidad}</td><td class='{clase}'>{estado}</td></tr>")
    return "<table>" + "".join(filas) + "</table>"
