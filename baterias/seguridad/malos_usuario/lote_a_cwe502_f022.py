import torch

def cargar_red_neuronal(ruta_archivo):
    pesos = torch.load(ruta_archivo)
    return pesos
