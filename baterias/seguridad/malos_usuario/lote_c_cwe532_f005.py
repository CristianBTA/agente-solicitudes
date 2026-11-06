import logging

def registrar_domicilio_protegido(id_solicitante, direccion_residencia, latitud, longitud):
    logging.debug(
        f"Refugio asignado a expediente {id_solicitante}: "
        f"calle={direccion_residencia}, lat={latitud}, lon={longitud}"
    )
    return True
