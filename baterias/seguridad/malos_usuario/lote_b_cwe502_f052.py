import pickle

def cargar_estado_entrenamiento(ruta_archivo):
    with open(ruta_archivo, "rb") as fuente:
        estado = pickle.load(fuente)
    return estado
