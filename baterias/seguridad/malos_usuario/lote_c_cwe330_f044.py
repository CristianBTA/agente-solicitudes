import time
import os

def crear_token_sesion_usuario(id_usuario):
    marca_tiempo = time.time_ns()
    pid = os.getpid()
    return f"SES-{id_usuario}-{marca_tiempo}-{pid}"
