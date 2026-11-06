def analizar(filas):
    return "".join(f"<td>{x['nombre']}</td>" for x in filas)
