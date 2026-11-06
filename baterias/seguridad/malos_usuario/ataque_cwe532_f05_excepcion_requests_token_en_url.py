import logging
import os

import requests

logger = logging.getLogger(__name__)
URL = "https://datos.example.org/resource/contratos.json"


def descargar(pagina):
    params = {"$limit": 1000, "$offset": pagina * 1000, "$$app_token": os.environ["SOCRATA_APP_TOKEN"]}
    try:
        resp = requests.get(URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Falló la descarga de la página %s: %s", pagina, e)
        raise
    return resp.json()
