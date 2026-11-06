import re

PATRON_HEXADECIMAL = re.compile(r"^([a-f0-9]+:*)+$")

def validar_trama_dispositivo(trama_texto):
    return bool(PATRON_HEXADECIMAL.match(trama_texto))
