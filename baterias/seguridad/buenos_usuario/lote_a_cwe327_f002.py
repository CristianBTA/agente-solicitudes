import hashlib
import os

def generar_derivacion_robusta(valor_original, sal=None):
    if sal is None:
        sal = os.urandom(16)
    resultado = hashlib.pbkdf2_hmac(
        "sha256",
        valor_original.encode("utf-8"),
        sal,
        100000
    )
    return sal.hex() + ":" + resultado.hex()
