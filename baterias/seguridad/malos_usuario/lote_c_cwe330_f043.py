import random

def generar_pin_confirmacion_sms():
    numero = int(random.uniform(100000, 999999))
    return str(numero)
