import os

DIRECTORIO_BALANCES = "/var/datos/balances"

def leer_balance_municipio(codigo_municipio):
    ruta = f"{DIRECTORIO_BALANCES}/{codigo_municipio}.pdf"
    with open(ruta, "rb") as archivo:
        return archivo.read()
