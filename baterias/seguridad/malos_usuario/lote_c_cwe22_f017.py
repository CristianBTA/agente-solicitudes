import os

def listar_ficheros_dependencia(nombre_subcarpeta):
    ruta_completa = f"/srv/compartido/{nombre_subcarpeta}"
    nombres = [entrada.name for entrada in os.scandir(ruta_completa) if entrada.is_file()]
    return nombres
