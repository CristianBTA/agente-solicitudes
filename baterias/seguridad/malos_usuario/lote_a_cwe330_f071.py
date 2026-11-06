import random
import string

def generar_token_api(longitud=32):
    alfabeto = string.ascii_letters + string.digits
    token = "".join(random.choice(alfabeto) for _ in range(longitud))
    return token
