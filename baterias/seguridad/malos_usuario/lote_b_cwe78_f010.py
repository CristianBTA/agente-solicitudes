import os

def descomprimir_partes_catastro(archivo_7z, carpeta_salida):
    instruccion = "7z x " + archivo_7z + " -o" + carpeta_salida
    return os.system(instruccion)
