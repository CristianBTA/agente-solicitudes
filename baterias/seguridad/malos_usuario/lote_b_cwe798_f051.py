import requests

def consultar_climatologia(codigo_postal):
    parametros = {
        "cp": codigo_postal,
        "api_key": "sec_app_9918273645bbcd",
        "formato": "json"
    }
    return requests.get("https://api.clima.internal/v1/forecast", params=parametros, timeout=15).json()
