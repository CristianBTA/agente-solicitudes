import re

def validar_fecha_contrato(fecha_texto):
    patron = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
    return bool(patron.match(fecha_texto))
