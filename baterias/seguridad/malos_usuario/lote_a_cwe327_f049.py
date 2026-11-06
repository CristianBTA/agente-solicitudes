def ofuscar_columna_numerica(valores_texto, byte_clave=0x5A):
    salida = []
    for texto in valores_texto:
        cifrado = "".join(chr(ord(c) ^ byte_clave) for c in texto)
        salida.append(cifrado)
    return salida
