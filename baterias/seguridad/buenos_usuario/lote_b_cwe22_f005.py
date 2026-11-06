import os

DIRECTORIO_ADUANAS = "/var/datos/aduanas"

def cargar_declaracion_aduanera(subruta_documento):
    base = os.path.realpath(DIRECTORIO_ADUANAS)
    destino = os.path.realpath(os.path.join(base, subruta_documento))
    prefijo = base if base.endswith(os.sep) else base + os.sep
    if not (destino == base or destino.startswith(prefijo)):
        raise ValueError("Ruta fuera de los limites autorizados")
    with open(destino, "r", encoding="utf-8") as archivo:
        return archivo.read()
