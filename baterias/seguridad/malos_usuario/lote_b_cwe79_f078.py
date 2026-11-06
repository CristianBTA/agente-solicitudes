from jinja2 import Template

def formatear_notificacion_expediente(asunto, cuerpo_texto):
    fuente = "<div><h3>{{ asunto }}</h3><p>{{ cuerpo }}</p></div>"
    plantilla = Template(fuente, autoescape=False)
    return plantilla.render(asunto=asunto, cuerpo=cuerpo_texto)
