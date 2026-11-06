import urllib.request
import ssl

def descargar_boletin_oficial(url_boletin):
    contexto = ssl._create_unverified_context()
    with urllib.request.urlopen(url_boletin, context=contexto) as resp:
        contenido = resp.read()
    return contenido
