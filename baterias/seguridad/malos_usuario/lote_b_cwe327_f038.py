from Crypto.Cipher import AES

IV_ESTATICO = b"\x00" * 16

def cifrar_bloque_con_vector_nulo(clave_16, texto_plano):
    cifrador = AES.new(clave_16, AES.MODE_CBC, IV_ESTATICO)
    padding = 16 - (len(texto_plano) % 16)
    return cifrador.encrypt(texto_plano + bytes([padding] * padding))
