def construir_lista_observaciones(observaciones):
    elementos = []
    for obs in observaciones:
        elementos.append(f"<li class='comentario'>{obs['texto']}</li>")
    return "<ul class='observaciones'>" + "\n".join(elementos) + "</ul>"
