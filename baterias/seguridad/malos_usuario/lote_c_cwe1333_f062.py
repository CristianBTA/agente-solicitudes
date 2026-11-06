import re

PATRON_NORMATIVA = re.compile(r"^((Ley\s*)?\d+[\s,]*)+$")

def validar_referencia_legal(texto_norma):
    return PATRON_NORMATIVA.search(texto_norma) is not None
