import os
import requests

def descargar_datos_geograficos(capa):
    token = os.environ.get("GEO_API_TOKEN")
    if not token:
        raise RuntimeError("Falta variable de configuracion")
    cabeceras = {"Authorization": f"Bearer {token}"}
    url = f"https://api.geodatos.es/capas/{capa}"
    return requests.get(url, headers=cabeceras, timeout=20).json()
