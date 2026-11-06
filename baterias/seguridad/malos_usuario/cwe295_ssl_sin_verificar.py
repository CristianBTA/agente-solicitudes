import ssl
import urllib.request
def analizar(url):
    return urllib.request.urlopen(url, context=ssl._create_unverified_context()).read()
