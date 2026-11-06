import urllib3

def crear_gestor_conexiones():
    http = urllib3.PoolManager(cert_reqs="CERT_NONE")
    return http
