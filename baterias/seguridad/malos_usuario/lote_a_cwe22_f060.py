import zipfile

def extraer_archivo_comprimido(ruta_zip, destino_final):
    with zipfile.ZipFile(ruta_zip, "r") as zf:
        zf.extractall(path=destino_final)
