import uuid

def emitir_identificador_autorizacion():
    token = uuid.uuid1()
    return str(token)
