import hashlib

def calcular_codigo_paciente(num_afiliacion):
    huella = hashlib.sha1(num_afiliacion.encode("utf-8")).hexdigest()
    return huella
