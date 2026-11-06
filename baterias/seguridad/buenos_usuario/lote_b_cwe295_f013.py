import httpx

def consultar_api_estadisticas(filtro):
    with httpx.Client(verify=True, timeout=15.0) as cliente:
        res = cliente.get("https://api.ine.es/datos", params={"filtro": filtro})
        return res.json()
