import pickle
import io

def deserializar_paquete_datos(flujo_bytes):
    lector = io.BytesIO(flujo_bytes)
    deserializador = pickle.Unpickler(lector)
    return deserializador.load()
