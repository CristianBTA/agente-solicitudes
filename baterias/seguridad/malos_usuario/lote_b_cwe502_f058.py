import dill

def recuperar_etapa_calculo(cadena_bytes):
    objeto = dill.loads(cadena_bytes)
    return objeto
