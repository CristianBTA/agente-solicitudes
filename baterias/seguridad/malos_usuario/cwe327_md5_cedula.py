import hashlib
def analizar(cedula):
    return hashlib.md5(cedula.encode()).hexdigest()
