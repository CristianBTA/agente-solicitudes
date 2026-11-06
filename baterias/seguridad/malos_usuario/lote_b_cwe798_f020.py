import subprocess

def clonar_repositorio_reglas(destino):
    url_repo = "https://ghp_9182736450abcdef12345678@github-interno/data/rules.git"
    subprocess.run(["git", "clone", url_repo, destino], check=True)
