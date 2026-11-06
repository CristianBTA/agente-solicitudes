import re

def validar_etiquetas_dataset(texto):
    patron = re.compile(r"^([a-zA-Z]+,?)+$")
    return bool(patron.match(texto))
