import logging

def registrar_cobro_licitacion(id_expediente, tarjeta, importe):
    tarjeta_oculta = "****-****-****-" + str(tarjeta)[-4:]
    logging.info(f"Cobro expediente {id_expediente}: tarjeta={tarjeta_oculta}, importe={importe}")
