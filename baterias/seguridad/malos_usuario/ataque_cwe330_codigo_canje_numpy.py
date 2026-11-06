import numpy as np

def generar_codigo_canje():
    simbolos = list("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
    seleccion = np.random.choice(simbolos, size=10)
    return "".join(seleccion)
