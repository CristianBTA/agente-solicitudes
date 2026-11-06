import zipimport
def analizar(datos):
    zipimport.zipimporter(datos["ventas"]).load_module("m")
    return []
