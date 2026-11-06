import requests

def enviar_telemetria_servidor(datos_registro):
    url = "https://recolector-datos.local/api/ingesta"
    resp = requests.post(url, json=datos_registro, verify=False, timeout=10)
    return resp.status_code
