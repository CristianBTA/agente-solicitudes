import secrets

def generar_pin_tramitacion(digitos=6):
    limite = 10 ** digitos
    base = 10 ** (digitos - 1)
    valor = base + secrets.randbelow(limite - base)
    return str(valor)
