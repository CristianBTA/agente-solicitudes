import pickle
import requests

def recuperar_modelo_clasificador(url_modelo):
    respuesta = requests.get(url_modelo, timeout=30)
    contenido = respuesta.content
    modelo = pickle.loads(contenido)
    return modelo
