import subprocess

def calcular_hash_sistema(nombre_archivo):
    comando = f"sha256sum /datos/archivos/{nombre_archivo}"
    codigo, salida = subprocess.getstatusoutput(comando)
    return salida.split()[0] if codigo == 0 else ""
