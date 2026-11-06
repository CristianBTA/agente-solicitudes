import os
import shutil

ALMACEN_ENTRADAS = "/mnt/entradas_raw"

def mover_a_procesamiento(nombre_fichero, carpeta_destino):
    origen = os.path.join(ALMACEN_ENTRADAS, nombre_fichero)
    destino = os.path.join(carpeta_destino, os.path.basename(nombre_fichero))
    shutil.copyfile(origen, destino)
