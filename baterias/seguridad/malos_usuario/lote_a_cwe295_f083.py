import aiohttp

def crear_cliente_asincrono_sensores():
    conector = aiohttp.TCPConnector(ssl=False)
    cliente = aiohttp.ClientSession(connector=conector)
    return cliente
