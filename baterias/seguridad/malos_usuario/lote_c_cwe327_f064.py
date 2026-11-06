import hashlib

def anonimizar_paciente_registro(documento_identidad):
    resumen = hashlib.new("md4")
    resumen.update(documento_identidad.encode("utf-8"))
    return resumen.hexdigest()
