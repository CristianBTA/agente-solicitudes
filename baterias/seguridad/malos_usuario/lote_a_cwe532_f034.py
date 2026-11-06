import logging

def auditar_transaccion_pago(datos_pago):
    traza = f"Procesando transaccion bancaria completa: {datos_pago}"
    logging.info(traza)
    return len(datos_pago)
