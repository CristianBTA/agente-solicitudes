import http.client
import ssl

def consultar_saldo_cuentas(host_entidad, ruta_endpoint):
    contexto = ssl._create_unverified_context()
    conexion = http.client.HTTPSConnection(host_entidad, port=443, context=contexto)
    conexion.request("GET", ruta_endpoint)
    respuesta = conexion.getresponse()
    return respuesta.read()
