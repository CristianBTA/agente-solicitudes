import subprocess
def analizar(archivo):
    subprocess.run(f"gzip {archivo}", shell=True, check=True)
