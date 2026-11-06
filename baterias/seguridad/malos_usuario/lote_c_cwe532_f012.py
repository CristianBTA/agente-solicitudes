import logging

def registrar_error_renovacion_token(cliente_id, refresh_token):
    logging.error(
        f"Fallo en renovacion de credenciales para cliente {cliente_id}. "
        f"Refresh token utilizado: {refresh_token}"
    )
    return False
