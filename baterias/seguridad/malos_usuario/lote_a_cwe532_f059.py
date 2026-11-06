import logging

def registrar_cobro_licitacion(id_expediente, tarjeta, importe):
    registro_msg = f"Cobro expediente {id_expediente}: tarjeta={tarjeta}, importe={importe}"
    logging.info(registro_msg)
    return True
