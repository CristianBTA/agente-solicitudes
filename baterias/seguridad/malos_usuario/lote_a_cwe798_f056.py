import requests

def sincronizar_catalogo_metadatos():
    endpoint = "https://datos.gob.es/api/v2/catalog/sync"
    encabezados = {"Authorization": "Bearer tok_live_8f3b20c91e4a77d612e55aa"}
    respuesta = requests.get(endpoint, headers=encabezados, timeout=30)
    return respuesta.json()
