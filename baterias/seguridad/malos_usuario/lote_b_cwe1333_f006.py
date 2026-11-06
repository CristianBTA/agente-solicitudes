import re

def validar_identificador_metrica(nombre_metrica):
    patron = re.compile(r"^([a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)+$")
    return bool(patron.match(nombre_metrica))
