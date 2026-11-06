import subprocess

import yaml

with open("config/pipeline.yml") as fh:
    CONFIG = yaml.safe_load(fh)


def respaldar_resultados():
    destino = CONFIG["ruta_respaldo"]
    comando = f"pg_dump solicitudes | gzip > {destino}"
    subprocess.run(comando, shell=True, check=True)
