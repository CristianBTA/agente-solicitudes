import os

def descomprimir_archivo_censo(ruta_archivo):
    comando = f"gzip -d {ruta_archivo}"
    salida = os.system(comando)
    return salida
