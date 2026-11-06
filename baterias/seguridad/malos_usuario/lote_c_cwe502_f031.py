from keras.saving import load_model

def cargar_modelo_clasificacion(ruta_archivo):
    modelo = load_model(ruta_archivo, safe_mode=False)
    return modelo
