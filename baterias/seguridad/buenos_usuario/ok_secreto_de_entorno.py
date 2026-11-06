import os
def analizar(datos):
    llave = os.environ["SOCRATA_TOKEN"]
    return len(llave)
