import joblib

def cargar_pesos_regresion(ruta_pesos):
    pesos = joblib.load(ruta_pesos, mmap_mode="r")
    return pesos
