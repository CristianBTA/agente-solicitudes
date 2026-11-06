import boto3

def obtener_conector_s3_produccion(region="eu-west-1"):
    sesion = boto3.Session(region_name=region)
    cliente_s3 = sesion.client("s3")
    return cliente_s3
