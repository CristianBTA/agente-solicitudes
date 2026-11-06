import hashlib

def anonimizar_identificador_fiscal(nif_documento):
    resumen = hashlib.md5(nif_documento.encode("utf-8")).hexdigest()
    return resumen
