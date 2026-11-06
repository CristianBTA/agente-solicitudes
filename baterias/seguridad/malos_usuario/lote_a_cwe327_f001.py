from Crypto.Cipher import DES

def proteger_clave_temporal(llave_8bytes, mensaje_bytes):
    cifrador = DES.new(llave_8bytes, DES.MODE_ECB)
    relleno = 8 - (len(mensaje_bytes) % 8)
    datos = mensaje_bytes + bytes([relleno] * relleno)
    return cifrador.encrypt(datos)
