import logging

def registrar_declaracion_jurada(rut_declarante, ingreso_anual, patrimonio_neto):
    logging.info(
        f"Declaracion jurada recibida: declarante={rut_declarante}, "
        f"ingreso_anual={ingreso_anual}, patrimonio={patrimonio_neto}"
    )
    return True
