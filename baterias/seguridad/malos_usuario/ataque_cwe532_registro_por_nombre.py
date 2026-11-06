def registrar_sesion_activa(ruta_log, usuario, jwt_token):
    timestamp_evento = "2024-03-01T12:00:00Z"
    linea = f"[{timestamp_evento}] Usuario={usuario} | TokenSesion={jwt_token}\n"
    with open(ruta_log, "a", encoding="utf-8") as f:
        f.write(linea)
    return True
