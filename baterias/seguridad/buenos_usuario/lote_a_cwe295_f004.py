import requests

def obtener_cotizaciones_divisas():
    url = "https://bce.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    respuesta = requests.get(url, timeout=30)
    return respuesta.content
