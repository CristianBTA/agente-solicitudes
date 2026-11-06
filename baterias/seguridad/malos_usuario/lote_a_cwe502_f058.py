import numpy as np

def leer_matrices_sensores(ruta_datos):
    matrices = np.load(ruta_datos, allow_pickle=True)
    return matrices
