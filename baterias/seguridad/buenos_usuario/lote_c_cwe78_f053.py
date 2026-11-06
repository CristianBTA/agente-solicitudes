import subprocess

def verificar_latencia_servidor(direccion_ip):
    proceso = subprocess.run(
        ["ping", "-c", "3", "--", direccion_ip],
        capture_output=True,
        text=True,
        check=False
    )
    return proceso.returncode == 0
