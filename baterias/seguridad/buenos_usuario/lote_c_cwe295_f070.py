import urllib.request
import ssl

def descargar_boletin_validado(url_boletin):
    contexto = ssl.create_default_context()
    solicitud = urllib.request.Request(
        url_boletin,
        headers={"User-Agent": "ColectorOficial/1.0"}
    )
    with urllib.request.urlopen(solicitud, context=contexto, timeout=30) as resp:
        return resp.read()
