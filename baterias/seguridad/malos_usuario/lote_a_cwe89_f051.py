import duckdb

def clasificar_exportaciones(conexion, columna_orden):
    sentencia = f"SELECT pais_destino, valor_eur, toneladas FROM comercio_exterior ORDER BY {columna_orden} DESC"
    return conexion.execute(sentencia).fetchall()
