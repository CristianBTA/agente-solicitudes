import tarfile
def analizar(ruta):
    with tarfile.open(ruta) as t:
        t.extractall()
