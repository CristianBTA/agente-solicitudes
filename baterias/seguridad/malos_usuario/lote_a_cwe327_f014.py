import hashlib

SAL_SISTEMA = "SAL_ESTATICA_2021"

def calcular_hash_credencial(clave_plana):
    material = SAL_SISTEMA + clave_plana
    return hashlib.md5(material.encode("utf-8")).hexdigest()
