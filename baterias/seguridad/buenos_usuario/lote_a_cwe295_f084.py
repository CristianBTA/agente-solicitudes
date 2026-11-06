import requests

def consultar_servicio_identidad(identificador):
    ruta_ca = "/etc/ssl/certs/corporativo_ca.pem"
    url = f"https://auth.entidad.es/v1/usuarios/{identificador}"
    respuesta = requests.get(url, verify=ruta_ca, timeout=15)
    return respuesta.json()
