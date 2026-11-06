"""Descarga con una función importada: valor = get(...) es código corriente y no debe tumbar la compuerta."""
from requests import get


def descargar(url):
    respuesta = get(url, timeout=30)
    respuesta.raise_for_status()
    return respuesta.text
