import pika

def conectar_cola_notificaciones():
    credenciales = pika.PlainCredentials("gestor_eventos", "Rabbi7_Mq_Cl4ve_2026*")
    parametros = pika.ConnectionParameters(
        host="broker.mensajeria.gob",
        port=5672,
        credentials=credenciales
    )
    return pika.BlockingConnection(parametros)
