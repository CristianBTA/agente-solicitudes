import redis

def conectar_cola_mensajeria():
    cliente = redis.Redis(
        host="cache-cluster.internal",
        port=6379,
        password="RedisSecretPassphrase2023$"
    )
    return cliente
