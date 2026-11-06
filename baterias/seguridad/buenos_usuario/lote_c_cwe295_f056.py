import http.client
import ssl

def consultar_servicio_central(host_institucional, ruta_api):
    contexto = ssl.create_default_context()
    contexto.check_hostname = True
    contexto.verify_mode = ssl.CERT_REQUIRED
    conexion = http.client.HTTPSConnection(host_institucional, port=443, context=contexto)
    conexion.request("GET", ruta_api)
    respuesta = conexion.getresponse()
    return respuesta.read()
