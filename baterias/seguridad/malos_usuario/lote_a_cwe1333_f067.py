import re

def validar_linea_descripcion(texto):
    patron = re.compile(r"^(\w+\s?)*$")
    return bool(patron.match(texto))
