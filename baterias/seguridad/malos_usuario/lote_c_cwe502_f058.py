import yaml

def cargar_especificacion_grafico(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as flujo:
        configuracion = yaml.unsafe_load(flujo)
    return configuracion
