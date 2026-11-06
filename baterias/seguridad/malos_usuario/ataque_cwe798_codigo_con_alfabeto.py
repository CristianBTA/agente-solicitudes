import numpy as np


def generar_codigo_canje():
    simbolos = list("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
    return "".join(np.random.choice(simbolos, size=10))
