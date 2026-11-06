CARPETA_PLANTILLAS = "/opt/plantillas"

def cargar_plantilla_contrato(nombre_plantilla):
    ubicacion = f"{CARPETA_PLANTILLAS}/{nombre_plantilla}"
    with open(ubicacion, "r", encoding="utf-8") as archivo:
        return archivo.read()
