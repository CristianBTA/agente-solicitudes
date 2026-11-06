import logging

def registrar_intento_sms_fallido(numero_movil, codigo_pin_sms):
    logging.warning(
        f"Intento de validacion fallido para telefono {numero_movil}: "
        f"codigo pin recibido '{codigo_pin_sms}'"
    )
    return False
