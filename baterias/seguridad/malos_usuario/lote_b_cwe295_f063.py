from pymongo import MongoClient

def conectar_cluster_almacenamiento(uri_cluster):
    cliente = MongoClient(uri_cluster, tls=True, tlsAllowInvalidHostnames=True)
    return cliente
