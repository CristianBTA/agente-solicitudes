from Crypto.Cipher import ARC4

def cifrar_comunicacion_interbancaria(clave_bytes, carga):
    cifrador = ARC4.new(clave_bytes)
    return cifrador.encrypt(carga)
