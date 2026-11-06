import re
from pathlib import Path

BASE_ANEXOS = Path("/var/archivos/anexos").resolve()

def leer_anexo_verificado(codigo_anexo):
    if not re.fullmatch(r"ANX-[0-9]{6}\.pdf", codigo_anexo):
        raise ValueError("Formato de anexo invalido")
    ruta = (BASE_ANEXOS / codigo_anexo).resolve()
    if not ruta.is_relative_to(BASE_ANEXOS):
        raise ValueError("Acceso no autorizado")
    return ruta.read_bytes()
