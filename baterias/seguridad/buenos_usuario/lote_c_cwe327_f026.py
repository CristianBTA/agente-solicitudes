import hashlib
import os

def generar_credencial_derivada(contrasena_plana):
    sal = os.urandom(16)
    clave_derivada = hashlib.scrypt(
        contrasena_plana.encode("utf-8"),
        salt=sal,
        n=16384,
        r=8,
        p=1
    )
    return sal.hex() + "$" + clave_derivada.hex()
