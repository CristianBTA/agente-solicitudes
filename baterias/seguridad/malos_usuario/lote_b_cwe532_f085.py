import logging

def registrar_conexion_nodo(servidor, usuario, clave_acceso):
    cadena_conexion = f"postgresql://{usuario}:{clave_acceso}@{servidor}/almacen"
    logging.info(f"Conectando a base de datos del nodo: {cadena_conexion}")
    return True
