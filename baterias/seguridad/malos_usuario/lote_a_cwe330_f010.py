import random
import hashlib

def crear_identificador_sesion(usuario_id):
    semilla = f"{usuario_id}:{random.random()}"
    return hashlib.sha256(semilla.encode()).hexdigest()
