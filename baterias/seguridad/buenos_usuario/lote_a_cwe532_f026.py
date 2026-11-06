import logging

def depurar_peticion_entrante(url, encabezados):
    filtradas = {k: ("[RESERVADO]" if k.lower() == "authorization" else v) for k, v in encabezados.items()}
    logging.debug(f"Peticion hacia {url} con cabeceras: {filtradas}")
