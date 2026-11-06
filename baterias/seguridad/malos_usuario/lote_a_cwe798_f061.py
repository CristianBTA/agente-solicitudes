import boto3

def crear_cliente_almacenamiento():
    cliente = boto3.client(
        "s3",
        aws_access_key_id="AKIAEJEMPLO0000000XXE",
        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )
    return cliente
