import requests
def analizar(url):
    return requests.get(url, timeout=30).json()
