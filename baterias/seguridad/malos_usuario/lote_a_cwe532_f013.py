import logging

def alertar_documento_duplicado(dni_titular, expediente):
    aviso = f"Conflicto de expediente {expediente} con titular DNI {dni_titular}"
    logging.warning(aviso)
    return aviso
