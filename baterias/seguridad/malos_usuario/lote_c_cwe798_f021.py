from azure.storage.blob import BlobServiceClient

def conectar_contenedor_auditorias():
    cadena_acceso = (
        "DefaultEndpointsProtocol=https;"
        "AccountName=almacenexpedientes;"
        "AccountKey=YnJ1aDR1S2V5TmVlZHNUb0JlU2VjcmV0VGhpczEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=;"
        "EndpointSuffix=core.windows.net"
    )
    cliente = BlobServiceClient.from_connection_string(cadena_acceso)
    return cliente.get_container_client("balances")
