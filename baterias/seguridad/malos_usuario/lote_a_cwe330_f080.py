import random
import string

def generar_contrasena_inicial():
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.sample(caracteres, 12))
