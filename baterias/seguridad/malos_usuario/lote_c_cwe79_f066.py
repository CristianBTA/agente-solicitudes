def armar_lista_alertas(alertas_recibidas):
    items = []
    for alerta in alertas_recibidas:
        items.append(f"<li>{alerta}</li>")
    filas = "".join(items)
    return f"<ul class='panel-alertas'>{filas}</ul>"
