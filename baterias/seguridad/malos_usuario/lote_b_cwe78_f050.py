import os

def localizar_archivos_ejercicio(directorio_base, anio):
    comando = f"find {directorio_base} -name '*_{anio}.csv'"
    with os.popen(comando) as flujo:
        coincidencias = flujo.read().splitlines()
    return coincidencias
