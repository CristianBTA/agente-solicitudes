def construir_catalogo_productos(articulos):
    bloque = "<tbody>"
    for art in articulos:
        bloque += "<tr><td>" + art["codigo"] + "</td><td>" + art["descripcion"] + "</td></tr>"
    bloque += "</tbody>"
    return bloque
