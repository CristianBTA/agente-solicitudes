import subprocess

def procesar_escaneo_catastro(origen_tif, destino_png):
    instruccion = f"convert {origen_tif} -resize 50% {destino_png}"
    codigo = subprocess.call(instruccion, shell=True)
    return codigo
