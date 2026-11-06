import re

PATRON_DESCRIPCION = re.compile(r"^([a-zA-Z0-9_]+ *)+$")

def validar_descripcion_rubro(texto_descripcion):
    coincidencia = PATRON_DESCRIPCION.match(texto_descripcion)
    return coincidencia is not None
