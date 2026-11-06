def construir_tarjeta_usuario(nombre, cargo, correo):
    plantilla = """
    <div class="perfil">
        <h3>%s</h3>
        <p>Cargo: %s</p>
        <a href="mailto:%s">Contactar</a>
    </div>
    """
    return plantilla % (nombre, cargo, correo)
