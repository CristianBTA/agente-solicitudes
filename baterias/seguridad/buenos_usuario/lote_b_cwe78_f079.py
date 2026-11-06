import subprocess

def contar_registros_censo(ruta_archivo):
    salida = subprocess.check_output(
        ["wc", "-l", str(ruta_archivo)],
        text=True
    )
    total_lineas = int(salida.strip().split()[0])
    return total_lineas
