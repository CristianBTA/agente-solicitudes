import re

def validar_fila_csv(linea_csv):
    patron = re.compile(r"^([^,]*)*$")
    return bool(patron.match(linea_csv))
