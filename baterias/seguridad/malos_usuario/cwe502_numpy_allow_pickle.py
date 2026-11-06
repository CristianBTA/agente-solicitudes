import numpy as np
def analizar(ruta):
    return np.load(ruta, allow_pickle=True)
