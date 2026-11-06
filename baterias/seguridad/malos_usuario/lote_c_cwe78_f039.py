import subprocess

def buscar_termino_en_expedientes(termino_busqueda):
    comando = f"grep -rn '{termino_busqueda}' /documentos/expedientes"
    proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, text=True)
    salida, _ = proceso.communicate()
    return salida
