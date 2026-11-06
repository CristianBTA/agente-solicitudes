from jinja2 import Environment, FileSystemLoader, select_autoescape

def renderizar_informe_auditoria(carpeta, contexto):
    entorno = Environment(
        loader=FileSystemLoader(carpeta),
        autoescape=select_autoescape(["html", "xml"])
    )
    plantilla = entorno.get_template("resumen.html")
    return plantilla.render(contexto)
