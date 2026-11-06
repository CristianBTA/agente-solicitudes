import yaml

def procesar_esquema_pipeline(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as flujo:
        definicion = yaml.load(flujo, Loader=yaml.Loader)
    return definicion
