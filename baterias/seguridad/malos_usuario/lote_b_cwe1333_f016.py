import re

def validar_telefono_contacto(telefono):
    patron = re.compile(r"^(\+?[0-9\s-]+)+$")
    return bool(patron.match(telefono))
