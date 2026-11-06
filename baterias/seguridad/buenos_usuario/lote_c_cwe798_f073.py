from pathlib import Path
from elasticsearch import Elasticsearch

def conectar_cluster_con_secreto_montado():
    ruta_token = Path("/run/secrets/elastic_api_key")
    if not ruta_token.exists():
        raise FileNotFoundError("Archivo de clave de servicio no disponible")
    clave_api = ruta_token.read_text(encoding="utf-8").strip()
    return Elasticsearch(
        "https://cluster-elastic.infra.gob:9200",
        api_key=clave_api
    )
