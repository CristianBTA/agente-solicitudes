import re

def comprobar_serie_contable(cadena):
    patron = re.compile(r"^(\d+)+$")
    return bool(patron.match(cadena))
