import logging

logger = logging.getLogger("autenticacion")

def registrar_intento_fallido(usuario, contrasena_intento):
    logger.error(f"Fallo de acceso para {usuario} con clave {contrasena_intento}")
