import httpx

def consultar_inventario_puerto(puerto_id):
    url = f"https://logistica-maritima.local/puertos/{puerto_id}"
    respuesta = httpx.get(url, verify=False, timeout=10.0)
    return respuesta.json()
