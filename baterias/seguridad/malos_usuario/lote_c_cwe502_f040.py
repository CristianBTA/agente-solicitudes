import torch
import io

def cargar_pesos_clasificador(buffer_bytes):
    flujo = io.BytesIO(buffer_bytes)
    modelo_estado = torch.load(flujo)
    return modelo_estado
