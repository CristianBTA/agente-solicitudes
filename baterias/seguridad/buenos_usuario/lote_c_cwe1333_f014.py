import re

PATRON_RUT_OFICIAL = re.compile(r"^[0-9]{7,8}-[0-9kK]$")

def validar_rut_proveedor_estado(rut_texto):
    return bool(PATRON_RUT_OFICIAL.fullmatch(rut_texto))
