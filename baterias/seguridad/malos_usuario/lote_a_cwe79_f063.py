def generar_tabla_proveedores(registros):
    filas_html = []
    for reg in registros:
        fila = f"<tr><td>{reg['nif']}</td><td>{reg['empresa']}</td><td>{reg['contacto']}</td></tr>"
        filas_html.append(fila)
    return "<table>" + "".join(filas_html) + "</table>"
