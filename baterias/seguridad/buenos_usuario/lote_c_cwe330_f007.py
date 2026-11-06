import secrets

LONGITUD_BYTES_API = 32

def generar_clave_api_entidad():
    bytes_aleatorios = secrets.token_bytes(LONGITUD_BYTES_API)
    return bytes_aleatorios.hex()
