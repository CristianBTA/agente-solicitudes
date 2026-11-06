def crear_tarjeta_beneficiario(nombre, estado_tramite):
    return (
        f"<div class='tarjeta-beneficio'>"
        f"<h3>{nombre}</h3>"
        f"<p>Estado: {estado_tramite}</p>"
        f"</div>"
    )
