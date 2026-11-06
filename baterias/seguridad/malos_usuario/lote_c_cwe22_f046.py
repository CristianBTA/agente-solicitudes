from pathlib import Path

def guardar_anexo_licitacion(nombre_adjunto, contenido_bytes):
    ruta_destino = Path(f"/var/archivos/anexos/{nombre_adjunto}")
    ruta_destino.write_bytes(contenido_bytes)
    return True
