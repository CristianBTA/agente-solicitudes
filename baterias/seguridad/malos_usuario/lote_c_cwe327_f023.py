from Crypto.Cipher import DES3

def cifrar_cuenta_proveedor(cuenta_bancaria, clave_16):
    cifrador = DES3.new(clave_16, DES3.MODE_ECB)
    datos_rellenos = cuenta_bancaria.ljust(24).encode("utf-8")
    return cifrador.encrypt(datos_rellenos)
