import hmac
import hashlib

def seudonimizar_registro_fiscal(llave_secreta, nif_valor):
    return hmac.new(
        llave_secreta,
        nif_valor.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()
