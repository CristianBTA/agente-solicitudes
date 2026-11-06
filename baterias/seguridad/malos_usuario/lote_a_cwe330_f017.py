import random
import time

def generar_clave_cifrado_temporal():
    random.seed(int(time.time()))
    clave = bytes(random.randint(0, 255) for _ in range(16))
    return clave
