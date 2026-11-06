import secrets
import string

def generar_codigo_recuperacion_cuenta(longitud=16):
    caracteres = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(caracteres) for _ in range(longitud))
