import os
import clickhouse_connect

def abrir_conexion_metricas_ambiente():
    clave = os.environ.get("CLICKHOUSE_PASSWORD")
    if not clave:
        raise ValueError("Variable de entorno CLICKHOUSE_PASSWORD no configurada")
    return clickhouse_connect.get_client(
        host="metricas.compras.gob",
        port=8443,
        username="usr_analitica",
        password=clave,
        database="auditoria"
    )
