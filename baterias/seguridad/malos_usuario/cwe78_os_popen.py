import os
def analizar(archivo):
    return os.popen(f"gzip {archivo}").read()
