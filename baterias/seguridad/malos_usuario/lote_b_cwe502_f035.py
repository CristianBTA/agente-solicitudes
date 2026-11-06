import marshal

def decodificar_funcion_transformacion(datos_binarios):
    codigo = marshal.loads(datos_binarios)
    return codigo
