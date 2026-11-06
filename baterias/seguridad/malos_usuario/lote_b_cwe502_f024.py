import jsonpickle

def restaurar_estado_proceso(payload_serializado):
    estado = jsonpickle.decode(payload_serializado)
    return estado
