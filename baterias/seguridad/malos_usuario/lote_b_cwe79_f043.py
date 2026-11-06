def componer_banner_aviso(mensaje, usuario):
    if not usuario:
        usuario = "anonimo"
    plantilla = '<div class="banner"><span>Usuario: {}</span><p>{}</p></div>'
    bloque_renderizado = plantilla.format(usuario, mensaje)
    return bloque_renderizado
