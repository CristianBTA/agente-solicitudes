import html

def generar_tabla_proveedores(registros):
    filas_html = []
    for reg in registros:
        nif_limpio = html.escape(str(reg["nif"]))
        empresa_limpia = html.escape(str(reg["empresa"]))
        contacto_limpio = html.escape(str(reg["contacto"]))
        fila = f"<tr><td>{nif_limpio}</td><td>{empresa_limpia}</td><td>{contacto_limpio}</td></tr>"
        filas_html.append(fila)
    return "<table>" + "".join(filas_html) + "</table>"
