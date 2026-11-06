from Crypto.Cipher import Blowfish

def cifrar_monto_contrato(monto_texto, clave_acceso):
    cifrador = Blowfish.new(clave_acceso, Blowfish.MODE_ECB)
    datos = monto_texto.ljust(16).encode("utf-8")
    return cifrador.encrypt(datos)
