import os

DIRECTORIO_BASE = "/var/datos/balances"

def leer_balance_restringido(nombre_archivo):
    base_real = os.path.realpath(DIRECTORIO_BASE)
    ruta_final = os.path.realpath(os.path.join(base_real, nombre_archivo))
    if not ruta_final.startswith(base_real + os.sep):
        raise ValueError("Ruta fuera de los limites permitidos")
    with open(ruta_final, "rb") as flujo:
        return flujo.read()
