import re
def analizar(texto):
    return re.match(r"^(a+)+$", texto) is not None
