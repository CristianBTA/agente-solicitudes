import httpx
def analizar(url):
    return httpx.get(url, verify=False).text
