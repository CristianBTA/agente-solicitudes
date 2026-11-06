import requests
def analizar(url):
    return requests.get(url, verify=False, timeout=30).text
