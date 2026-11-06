import clickhouse_connect

def abrir_conexion_metricas():
    cliente = clickhouse_connect.get_client(
        host="metricas.compras.gob",
        port=8443,
        username="usr_analitica",
        password="ClickHouse_Pass_Prod_2026!#",
        database="auditoria"
    )
    return cliente
