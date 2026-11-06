import markupsafe

def componer_banner_aviso(mensaje, usuario):
    u_escapado = markupsafe.escape(usuario)
    m_escapado = markupsafe.escape(mensaje)
    return f'<div class="banner"><span>Usuario: {u_escapado}</span><p>{m_escapado}</p></div>'
