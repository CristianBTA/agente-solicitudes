import re

PATRON_FECHA_ISO = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")

def validar_fecha_corte_censo(texto_fecha):
    return PATRON_FECHA_ISO.fullmatch(texto_fecha) is not None
