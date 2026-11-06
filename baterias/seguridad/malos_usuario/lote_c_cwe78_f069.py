import subprocess

def comprobar_disponibilidad_nodo(direccion_ip):
    orden = f"ping -c 3 {direccion_ip}"
    resultado = subprocess.getoutput(orden)
    return resultado
