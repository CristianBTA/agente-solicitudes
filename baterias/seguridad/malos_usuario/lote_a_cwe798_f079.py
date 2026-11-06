import requests

def descargar_censo_agrario(campana):
    url = f"https://repo-estadistica.local/agricola/{campana}.csv"
    autenticacion = ("ingesta_batch", "ClaveAgraria2024!")
    respuesta = requests.get(url, auth=autenticacion, timeout=45)
    return respuesta.content
