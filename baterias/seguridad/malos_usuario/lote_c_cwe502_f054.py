import _pickle

def recuperar_sesion_analista(carga_binaria):
    datos_sesion = _pickle.loads(carga_binaria)
    return datos_sesion
