import os

def construir_config_almacen():
    usuario = os.getenv("DB_USER", "lector_defecto")
    token_acceso = os.getenv("DB_TOKEN")
    if not token_acceso:
        raise ValueError("Falta credencial en entorno")
    return {"user": usuario, "token": token_acceso}
