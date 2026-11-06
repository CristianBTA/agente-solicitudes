import logging

def notificar_enlace_cambio(correo, token_cambio):
    url = f"https://servicios.local/reset?tok={token_cambio}"
    logging.info(f"Generado enlace de cambio para {correo}: {url}")
