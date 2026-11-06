from pathlib import Path

DIRECTORIO_RECURSOS = Path("/srv/recursos_estaticos")

def obtener_activo_estatico(identificador_recurso):
    ruta_archivo = DIRECTORIO_RECURSOS.joinpath(identificador_recurso)
    return ruta_archivo.read_bytes()
