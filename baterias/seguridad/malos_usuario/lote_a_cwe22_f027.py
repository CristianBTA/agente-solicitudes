import os

DIRECTORIO_DATOS = "/var/data/informes"

def leer_informe_publico(nombre_documento):
    ruta = os.path.join(DIRECTORIO_DATOS, nombre_documento)
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()
