import re

def validar_hash_transaccion(cadena_hex):
    patron = re.compile(r"^([0-9a-fA-F]+)+$")
    return bool(patron.match(cadena_hex))
