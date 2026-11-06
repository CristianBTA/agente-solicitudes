import requests

def crear_sesion_descarga_actas():
    sesion = requests.Session()
    sesion.verify = False
    return sesion
