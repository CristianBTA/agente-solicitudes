import random

def generar_codigo_recuperacion():
    codigo = random.randint(100000, 999999)
    return str(codigo)
