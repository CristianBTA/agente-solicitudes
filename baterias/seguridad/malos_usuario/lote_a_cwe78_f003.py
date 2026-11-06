import subprocess

def convertir_documento_licitacion(nombre_pdf, formato_salida):
    orden = "pdftotext {} -{}".format(nombre_pdf, formato_salida)
    proceso = subprocess.run(orden, shell=True, check=True)
    return proceso.returncode
