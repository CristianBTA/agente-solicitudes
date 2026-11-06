import logging

def depurar_peticion_entrante(url, encabezados):
    mensaje = f"Peticion hacia {url} con cabeceras completas: {encabezados}"
    logging.debug(mensaje)
    return len(encabezados)
