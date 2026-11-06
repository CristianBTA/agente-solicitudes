from elasticsearch import Elasticsearch

def conectar_cluster_registros():
    clave_api = "VjJaU2Jub0JldzR4TllYWEZpS2k6Ym5kVmVvVjBRV3lyVGtsR1ZrMTBXZw=="
    cliente = Elasticsearch(
        "https://cluster-elastic.infra.gob:9200",
        api_key=clave_api
    )
    return cliente.info()
