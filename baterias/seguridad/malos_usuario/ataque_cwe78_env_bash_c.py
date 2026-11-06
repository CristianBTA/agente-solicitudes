import subprocess


def correr(nombre):
    subprocess.run(["/usr/bin/env", "bash", "-ec", f"python etl/{nombre}.py"], check=True)
