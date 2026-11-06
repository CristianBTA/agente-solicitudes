import subprocess

def replicar_carpeta_servidor(carpeta_origen, destino_remoto):
    comando = f"rsync -avz {carpeta_origen} {destino_remoto}"
    subprocess.check_call(comando, shell=True)
