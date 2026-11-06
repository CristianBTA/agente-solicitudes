import json

def leer_configuracion_etapas(ruta_json):
    with open(ruta_json, "r", encoding="utf-8") as archivo:
        configuracion = json.load(archivo)
    return configuracion
