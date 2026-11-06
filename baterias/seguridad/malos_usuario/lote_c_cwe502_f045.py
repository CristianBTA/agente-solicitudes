import cloudpickle

def restaurar_estado_pipeline(datos_serializados):
    objeto_pipeline = cloudpickle.loads(datos_serializados)
    return objeto_pipeline
