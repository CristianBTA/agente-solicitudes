from pathlib import Path

DIRECTORIO_DATOS = Path("/var/data/informes").resolve()

def leer_informe_publico(nombre_documento):
    ruta = (DIRECTORIO_DATOS / nombre_documento).resolve()
    if not ruta.is_relative_to(DIRECTORIO_DATOS):
        raise ValueError("Acceso fuera del directorio permitido")
    return ruta.read_text(encoding="utf-8")
