from Crypto.Cipher import AES
import os

def cifrar_con_aes_gcm(clave_32, datos):
    nonce = os.urandom(12)
    cifrador = AES.new(clave_32, AES.MODE_GCM, nonce=nonce)
    texto_cifrado, etiqueta = cifrador.encrypt_and_digest(datos)
    return nonce + etiqueta + texto_cifrado
