import shutil

def extraer_paquete_declaraciones(archivo_comprimido):
    directorio_destino = "/var/procesamiento/declaraciones"
    shutil.unpack_archive(archivo_comprimido, extract_dir=directorio_destino)
    return directorio_destino
