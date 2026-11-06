import xml.sax.saxutils as saxutils

def generar_item_boletin_filtrado(titulo, descripcion):
    entidades = {"'": "&apos;", '"': "&quot;"}
    tit_limpio = saxutils.escape(titulo, entidades)
    desc_limpia = saxutils.escape(descripcion, entidades)
    return f"<item><title>{tit_limpio}</title><description>{desc_limpia}</description></item>"
