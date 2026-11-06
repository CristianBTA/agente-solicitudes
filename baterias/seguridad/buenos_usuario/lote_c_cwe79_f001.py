import html

def generar_lista_alertas_limpia(alertas_recibidas):
    filas = "".join(f"<li>{html.escape(str(a), quote=True)}</li>" for a in alertas_recibidas)
    return f"<ul class='panel-alertas'>{filas}</ul>"
