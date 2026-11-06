import hashlib

def guardar_hash_credencial(contrasena_plana):
    resumen = hashlib.sha256(contrasena_plana.encode("utf-8"))
    return resumen.hexdigest()
