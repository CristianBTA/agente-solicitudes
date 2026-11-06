def inyectar_contexto_usuario(identificador, nombre_completo):
    bloque_script = (
        f"<script>\n"
        f"  var usuarioActual = {{ id: '{identificador}', nombre: '{nombre_completo}' }};\n"
        f"</script>"
    )
    return bloque_script
