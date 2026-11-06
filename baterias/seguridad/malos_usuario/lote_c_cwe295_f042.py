import requests

def actualizar_registro_presupuestario(url_recurso, payload_json):
    respuesta = requests.put(
        url_recurso,
        json=payload_json,
        verify=False,
        timeout=15
    )
    return respuesta.status_code
