import subprocess

def contar_lineas_archivo_censo(anio):
    anio_valido = int(anio)
    ruta = f"/var/datos/censo_{anio_valido}.csv"
    salida = subprocess.check_output(
        ["wc", "-l", ruta],
        text=True
    )
    return int(salida.strip().split()[0])
