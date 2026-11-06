import tomllib

def cargar_configuracion_analisis(texto_toml):
    configuracion = tomllib.loads(texto_toml)
    if "parametros" not in configuracion:
        raise KeyError("Seccion parametros no encontrada")
    return configuracion
