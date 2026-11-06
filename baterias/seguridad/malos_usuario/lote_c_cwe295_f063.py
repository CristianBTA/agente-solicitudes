import boto3

def instanciar_cliente_s3_pruebas():
    cliente = boto3.client(
        "s3",
        endpoint_url="https://s3.local.infra:9000",
        verify=False
    )
    return cliente.list_buckets()
