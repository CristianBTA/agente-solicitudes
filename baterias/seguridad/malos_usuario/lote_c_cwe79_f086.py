import markdown

def renderizar_observacion_ciudadana(autor, comentario):
    texto = f"### Observacion de {autor}\n\n{comentario}"
    html_resultado = markdown.markdown(texto)
    return html_resultado
