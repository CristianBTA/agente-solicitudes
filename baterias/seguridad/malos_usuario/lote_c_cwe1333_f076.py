import re

PATRON_RADICADO = re.compile(r"^(\d+[\.\-]?)+$")

def validar_codigo_expediente(cadena_codigo):
    return bool(PATRON_RADICADO.match(cadena_codigo))
