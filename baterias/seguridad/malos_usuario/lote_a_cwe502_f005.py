import shelve

def consultar_registro_historico(ruta_almacen, clave):
    with shelve.open(ruta_almacen, flag="r") as base_datos:
        valor = base_datos.get(clave)
    return valor
