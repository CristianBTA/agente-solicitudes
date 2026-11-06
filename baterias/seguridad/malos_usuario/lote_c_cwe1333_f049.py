import re

PATRON_CORREO_SIMPLE = re.compile(r"^([a-z0-9]+)+@[a-z0-9]+$")

def comprobar_correo_institucional(direccion_correo):
    resultado = PATRON_CORREO_SIMPLE.match(direccion_correo)
    return bool(resultado)
