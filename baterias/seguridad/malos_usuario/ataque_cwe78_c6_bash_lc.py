import subprocess


def ejecutar_etl(nombre_script):
    subprocess.run(["bash", "-lc", f"conda run python etl/{nombre_script}.py"], check=True)
