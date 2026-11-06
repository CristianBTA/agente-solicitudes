def analizar(filas):
    for x in filas:
        print("procesando", x["cedula"], x["nombre"])
    return len(filas)
