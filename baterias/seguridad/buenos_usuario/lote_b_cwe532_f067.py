import logging

def registrar_orden_transferencia(beneficiario, iban, cuantia):
    titular = str(beneficiario)
    titular_oculto = titular[:1] + "*" * max(3, len(titular) - 2) + titular[-1:] if len(titular) > 2 else "***"
    cuenta = str(iban)
    cuenta_oculta = cuenta[:4] + "*" * max(4, len(cuenta) - 8) + cuenta[-4:] if len(cuenta) > 8 else "****"
    logging.info(f"Orden emitida a {titular_oculto} en cuenta {cuenta_oculta} por {cuantia} EUR")
