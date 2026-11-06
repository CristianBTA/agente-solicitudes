import aiohttp

async def obtener_inventario_local(url_servicio):
    conector = aiohttp.TCPConnector(verify_ssl=False)
    async with aiohttp.ClientSession(connector=conector) as sesion:
        async with sesion.get(url_servicio) as resp:
            return await resp.text()
