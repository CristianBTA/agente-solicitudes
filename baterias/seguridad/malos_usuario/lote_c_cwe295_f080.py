import urllib.request
import ssl

def descargar_acta_municipal(url_documento):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url_documento, context=ctx) as respuesta:
        return respuesta.read()
