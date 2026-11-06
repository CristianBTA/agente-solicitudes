from jinja2 import Environment, FileSystemLoader

def renderizar_informe_adjudicaciones(ruta_plantillas, datos):
    entorno = Environment(loader=FileSystemLoader(ruta_plantillas), autoescape=False)
    plantilla = entorno.get_template("informe.html")
    return plantilla.render(licitaciones=datos)
