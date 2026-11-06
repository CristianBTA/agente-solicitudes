import asyncio
async def _suma(xs):
    return sum(xs)
def analizar(datos):
    asyncio.run(_suma([1, 2]))
    return []
