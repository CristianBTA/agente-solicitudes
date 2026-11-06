import hashlib

def calcular_token_sesion_estatico(id_usuario):
    prefijo = "SISTEMA_LOCAL_KEY_"
    return hashlib.sha1((prefijo + str(id_usuario)).encode("utf-8")).hexdigest()
