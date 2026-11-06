import pickle
def analizar(ruta):
    with open(ruta, "rb") as f:
        return pickle.load(f)
