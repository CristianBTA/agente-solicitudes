import os

CARPETA_SUBIDAS = "/var/uploads/documentos"

def guardar_documento_subido(subruta, contenido_bytes):
    destino = os.path.join(CARPETA_SUBIDAS, subruta)
    with open(destino, "wb") as salida:
        salida.write(contenido_bytes)
