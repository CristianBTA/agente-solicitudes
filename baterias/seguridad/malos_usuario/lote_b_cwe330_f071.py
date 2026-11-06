import random

def generar_clave_servicio():
    entero = random.getrandbits(128)
    return f"{entero:032x}"
