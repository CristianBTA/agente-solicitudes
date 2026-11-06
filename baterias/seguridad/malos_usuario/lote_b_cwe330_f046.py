import random
import string

def generar_secreto_webhook():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=24))
