import hmac
import hashlib

def seudonimizar_contribuyente_tributario(rut_contribuyente, clave_maestra):
    resumen = hmac.new(
        clave_maestra,
        rut_contribuyente.encode("utf-8"),
        hashlib.sha384
    )
    return resumen.hexdigest()
