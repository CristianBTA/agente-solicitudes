from html import escape
def analizar(filas):
    return "".join(f"<td>{escape(x['nombre'])}</td>" for x in filas)
