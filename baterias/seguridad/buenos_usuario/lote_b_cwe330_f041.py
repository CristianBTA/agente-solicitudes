import secrets

def crear_enlace_invitacion(base_url):
    token = secrets.token_urlsafe(32)
    return f"{base_url}?token={token}"
