import subprocess

def descomprimir_archivo_censo(ruta_archivo):
    resultado = subprocess.run(["gzip", "-d", str(ruta_archivo)], check=True)
    return resultado.returncode
