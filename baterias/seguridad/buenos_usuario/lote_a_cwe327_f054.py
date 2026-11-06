import hmac
import hashlib

def calcular_huella_identificador(llave_secreta, identificador):
    clave_bytes = llave_secreta.encode("utf-8")
    mensaje = identificador.encode("utf-8")
    return hmac.new(clave_bytes, mensaje, hashlib.sha256).hexdigest()
