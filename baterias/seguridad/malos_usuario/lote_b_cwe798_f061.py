def obtener_configuracion_kafka():
    config = {
        "bootstrap.servers": "broker.internal:9092",
        "security.protocol": "SASL_PLAINTEXT",
        "sasl.mechanism": "PLAIN",
        "sasl.username": "ingest_stream",
        "sasl.password": "KafkaStreamPass2025!"
    }
    return config
