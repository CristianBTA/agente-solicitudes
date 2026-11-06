from pymongo import MongoClient

def conectar_cluster_trazabilidad(uri_servidor):
    cliente = MongoClient(
        uri_servidor,
        tls=True,
        tlsAllowInvalidCertificates=True
    )
    return cliente
