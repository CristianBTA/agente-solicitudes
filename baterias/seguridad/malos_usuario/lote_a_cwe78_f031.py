import tarfile
from pathlib import Path

def extraer_paquete_datos(ruta_tar, carpeta_destino):
    destino = Path(carpeta_destino).resolve()
    with tarfile.open(ruta_tar, "r:*") as archivo:
        archivo.extractall(path=destino)
