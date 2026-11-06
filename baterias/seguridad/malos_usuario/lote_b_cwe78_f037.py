import subprocess

def descomprimir_lote_zip(archivo_zip, destino):
    cmd = f"unzip -q {archivo_zip} -d {destino}"
    return subprocess.run(cmd, shell=True).returncode
