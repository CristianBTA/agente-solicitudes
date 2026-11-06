import random

def generar_comprobante_aleatorio():
    codigo = int(abs(random.gauss(500000, 150000))) % 1000000
    return f"REC-{codigo:06d}"
