import joblib

def cargar_transformador_columnas(ruta_cache):
    transformador = joblib.load(ruta_cache)
    return transformador
