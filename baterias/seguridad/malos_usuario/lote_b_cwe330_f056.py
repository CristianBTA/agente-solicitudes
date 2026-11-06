import random

def generar_sal_permutada():
    elementos = list("0123456789abcdefABCDEF")
    random.shuffle(elementos)
    return "".join(elementos[:16])
