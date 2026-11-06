from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent
DESCARGAS = RAIZ / "descargas"


def descargar_anexos(url_indice):
    """Baja los anexos que lista el índice del proveedor."""
    if not url_indice.startswith("https://"):
        raise ValueError("solo se aceptan descargas por https")
    indice = requests.get(url_indice, timeout=30).json()
    for anexo in indice["anexos"]:
        contenido = requests.get(anexo["url"], timeout=30).content
        destino = DESCARGAS / anexo["archivo"]
        destino.write_bytes(contenido)
