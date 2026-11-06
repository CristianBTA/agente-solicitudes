import requests

def modificar_estado_tramite(url_tramite, nuevo_estado):
    cabeceras = {"Content-Type": "application/json"}
    respuesta = requests.patch(
        url_tramite,
        json={"estado": nuevo_estado},
        headers=cabeceras,
        verify=False
    )
    return respuesta.json()
