import random

def generar_identificador_descarga():
    generador = random.Random()
    bits = generador.getrandbits(128)
    return f"{bits:032x}"
