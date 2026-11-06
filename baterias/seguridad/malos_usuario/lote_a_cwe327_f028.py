from Crypto.Cipher import AES

def cifrar_registro_nomina(clave_16bytes, datos_crudos):
    cifrador = AES.new(clave_16bytes, AES.MODE_ECB)
    longitud_relleno = 16 - (len(datos_crudos) % 16)
    datos_rellenos = datos_crudos + bytes([longitud_relleno] * longitud_relleno)
    return cifrador.encrypt(datos_rellenos)
