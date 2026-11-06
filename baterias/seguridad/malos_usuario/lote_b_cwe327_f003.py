import codecs

def enmascarar_iban_con_rot13(iban_completo):
    iban_limpio = iban_completo.strip()
    ofuscado = codecs.encode(iban_limpio, "rot_13")
    return ofuscado
