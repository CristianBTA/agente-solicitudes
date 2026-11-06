import random

def generar_pin_transaccion():
    pin = random.randrange(1000, 9999)
    return f"{pin:04d}"
