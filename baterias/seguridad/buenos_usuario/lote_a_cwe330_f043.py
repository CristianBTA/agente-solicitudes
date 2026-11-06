import secrets
import string

def generar_contrasena_temporal(longitud=16):
    alfabeto = string.ascii_letters + string.digits
    generador = secrets.SystemRandom()
    return "".join(generador.choice(alfabeto) for _ in range(longitud))
