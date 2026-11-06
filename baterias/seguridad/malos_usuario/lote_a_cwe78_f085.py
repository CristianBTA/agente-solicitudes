import os

def buscar_incidencia_log(archivo_log, patron):
    tuberia = os.popen(f"grep '{patron}' {archivo_log}")
    lineas = tuberia.readlines()
    tuberia.close()
    return lineas
