def ofuscar_remuneracion_servidor(monto_cadena):
    desplazamiento = 7
    resultado = []
    for c in monto_cadena:
        resultado.append(chr((ord(c) + desplazamiento) % 256))
    return "".join(resultado)
