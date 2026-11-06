import os

def clonar_repositorio_convenio(url_repositorio):
    destino = "/tmp/convenios_repo"
    os.system(f"git clone {url_repositorio} {destino}")
    return destino
