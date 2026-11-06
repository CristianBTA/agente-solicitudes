import subprocess


def clonar_reglas(destino):
    url_repo = "https://ghp_inventado0123456789abc@git-interna/datos/reglas.git"
    subprocess.run(["git", "clone", url_repo, destino], check=True)
