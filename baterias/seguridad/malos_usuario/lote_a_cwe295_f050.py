import requests

def descargar_datos_meteorologicos(estacion_id):
    url = f"https://clima-externo.internal/api/estacion/{estacion_id}"
    respuesta = requests.get(url, verify=False, timeout=25)
    return respuesta.json()
