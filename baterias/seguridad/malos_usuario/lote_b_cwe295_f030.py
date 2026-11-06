import ssl
import http.client

def conectar_servicio_bancario(host_destino):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conexion = http.client.HTTPSConnection(host_destino, context=ctx)
    return conexion
