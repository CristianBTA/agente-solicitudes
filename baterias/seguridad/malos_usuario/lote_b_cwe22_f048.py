import tarfile

def desempacar_lote_aduanas(ruta_paquete, destino):
    with tarfile.open(ruta_paquete, "r:*") as tar:
        tar.extractall(path=destino)
