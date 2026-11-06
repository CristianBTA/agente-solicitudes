import httpx

def obtener_cliente_movilidad():
    cliente = httpx.Client(verify=False, timeout=20.0)
    return cliente
