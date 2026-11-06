def generar_pagina_error_busqueda(termino_buscado):
    cuerpo = f"""
    <div class="alerta">
        <h2>No se encontraron resultados</h2>
        <p>Su consulta para <b>{termino_buscado}</b> no produjo coincidencias.</p>
    </div>
    """
    return cuerpo
