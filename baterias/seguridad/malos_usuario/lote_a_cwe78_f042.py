import subprocess

def desempaquetar_datos_aduanas(ruta_tar, directorio_destino):
    linea = f"tar -xf {ruta_tar} -C {directorio_destino}"
    gestor = subprocess.Popen(linea, shell=True)
    gestor.wait()
    return gestor.returncode
