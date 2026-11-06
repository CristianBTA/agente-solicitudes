def generar_item_boletin(titulo, descripcion):
    bloque = (
        f"<item>"
        f"<title>{titulo}</title>"
        f"<description>{descripcion}</description>"
        f"</item>"
    )
    return bloque
