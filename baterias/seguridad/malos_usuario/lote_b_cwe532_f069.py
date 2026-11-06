import logging

def registrar_orden_transferencia(beneficiario, iban, cuantia):
    mensaje = f"Orden emitida a {beneficiario} en cuenta {iban} por {cuantia} EUR"
    logging.info(mensaje)
    return mensaje
