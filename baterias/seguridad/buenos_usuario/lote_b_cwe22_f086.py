import os

CARPETA_SUBIDAS = "/var/uploads/documentos"

def guardar_documento_subido(subruta, contenido_bytes):
    base = os.path.realpath(CARPETA_SUBIDAS)
    destino = os.path.realpath(os.path.join(base, subruta))
    if os.path.commonpath([base, destino]) != base:
        raise ValueError("Ruta de archivo no autorizada")
    with open(destino, "wb") as salida:
        salida.write(contenido_bytes)
