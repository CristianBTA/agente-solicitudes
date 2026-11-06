import zlib

def calcular_identificador_elector(cedula_ciudadania):
    valor_crc = zlib.crc32(cedula_ciudadania.encode("utf-8"))
    return f"VOT-{valor_crc:08X}"
