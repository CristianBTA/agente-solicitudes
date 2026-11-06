import re

def validar_ruta_relativa(ruta_texto):
    patron = re.compile(r"^([a-zA-Z0-9_-]+/?)+$")
    return bool(patron.match(ruta_texto))
