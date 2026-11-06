def trazar_llamada_remota(url_servicio, token_privado):
    canal_log = "[DEBUGLOG]"
    mensaje = f"{canal_log} Llamando a {url_servicio} utilizando token: {token_privado}"
    print(mensaje)
    return len(token_privado)
