import hashlib
import os
def analizar(cedula):
    return hashlib.sha256(os.environ["SAL"].encode() + cedula.encode()).hexdigest()
