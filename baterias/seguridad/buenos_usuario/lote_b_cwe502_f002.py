import torch

def cargar_pesos_modelo(ruta_modelo):
    tensores = torch.load(ruta_modelo, weights_only=True)
    return tensores
