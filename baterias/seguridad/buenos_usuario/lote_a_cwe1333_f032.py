import re

def validar_codigo_expediente(cadena_entrada):
    patron = re.compile(r"^[a-zA-Z0-9]{1,64}$")
    return bool(patron.match(cadena_entrada))
