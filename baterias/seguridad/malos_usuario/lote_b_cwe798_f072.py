import snowflake.connector

def conectar_almacen_snowflake():
    conexion = snowflake.connector.connect(
        user="analytics_loader",
        password="SnowflakeSecretPassword789!",
        account="xy12345.eu-west-1",
        warehouse="COMPUTE_WH"
    )
    return conexion
