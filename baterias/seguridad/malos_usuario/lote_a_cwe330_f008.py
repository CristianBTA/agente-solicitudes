import numpy as np

def crear_token_numerico():
    valores = np.random.randint(0, 10, size=16)
    return "".join(str(v) for v in valores)
