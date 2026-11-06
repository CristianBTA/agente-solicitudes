import pandas as pd


def tag(nombre, contenido):
    return f"<{nombre}>{contenido}</{nombre}>"


def tabla_html(df):
    cabecera = tag("tr", "".join(tag("th", c) for c in df.columns))
    filas = [tag("tr", "".join(tag("td", v) for v in fila)) for fila in df.itertuples(index=False)]
    return tag("table", cabecera + "".join(filas))


def reporte(ruta_csv):
    return tabla_html(pd.read_csv(ruta_csv))
