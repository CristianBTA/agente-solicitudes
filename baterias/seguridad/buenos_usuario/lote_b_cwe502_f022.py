import numpy as np

def leer_array_calibracion(ruta_matriz):
    arreglo = np.load(ruta_matriz, allow_pickle=False)
    return arreglo
