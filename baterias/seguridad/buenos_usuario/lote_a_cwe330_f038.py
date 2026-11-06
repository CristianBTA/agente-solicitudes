import secrets

def generar_token_api(num_bytes=32):
    if num_bytes < 16:
        num_bytes = 16
    token = secrets.token_hex(num_bytes)
    return token
