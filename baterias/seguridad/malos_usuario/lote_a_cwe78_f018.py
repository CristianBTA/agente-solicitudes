import subprocess

def descargar_capa_geografica(url_origen, archivo_local):
    cmd = f"curl -sSL '{url_origen}' -o '{archivo_local}'"
    resultado = subprocess.check_output(cmd, shell=True)
    return resultado
