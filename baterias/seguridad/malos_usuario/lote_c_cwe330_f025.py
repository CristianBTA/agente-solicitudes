import random
import string

def crear_token_invitacion_fijo():
    random.seed(12345)
    alfabeto = string.ascii_letters + string.digits
    return "".join(random.choices(alfabeto, k=24))
