import re

def validar_correo_licitador(direccion):
    patron = re.compile(r"^([a-zA-Z0-9_.-]+)+@([a-zA-Z0-9_-]+)+(\.[a-zA-Z]{2,4})+$")
    return bool(patron.match(direccion))
