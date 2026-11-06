import re

PATRON_PALABRAS = re.compile(r"^([a-zA-Z]+-?)+$")

def validar_terminos_clave(cadena_entrada):
    return PATRON_PALABRAS.match(cadena_entrada) is not None
