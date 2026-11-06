import sys

def notificar_error_cobro(numero_referencia, cvv_tarjeta, fecha_vencimiento):
    sys.stderr.write(
        f"Cobro fallido ref={numero_referencia}: "
        f"cvv={cvv_tarjeta} exp={fecha_vencimiento}\n"
    )
