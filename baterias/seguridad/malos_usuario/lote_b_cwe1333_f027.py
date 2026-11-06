import re

def validar_codigo_postal_extranjero(cp):
    patron = re.compile(r"^(\d+\s*)+$")
    return bool(patron.match(cp))
