import re

def verificar_url_repositorio(url):
    patron = re.compile(r"^(https?://)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*/?$")
    return bool(patron.match(url))
