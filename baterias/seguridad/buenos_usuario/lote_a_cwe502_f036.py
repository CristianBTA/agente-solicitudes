import yaml

def cargar_definicion_campos(ruta_yaml):
    with open(ruta_yaml, "r", encoding="utf-8") as f:
        contenido = yaml.safe_load(f)
    return contenido
