import subprocess

def extraer_texto_acta(archivo_pdf):
    orden = f"pdftotext {archivo_pdf} -"
    salida = subprocess.check_output(orden, shell=True, text=True)
    return salida
