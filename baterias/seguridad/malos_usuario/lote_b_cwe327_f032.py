import hashlib

def almacenar_clave_usuario(identificador, credencial):
    resumen = hashlib.sha1(credencial.encode("utf-8")).hexdigest()
    registro = {"id": identificador, "hash": resumen}
    return registro
