import duckdb

def exportar_subvenciones_departamento(conn, departamento, salida_csv):
    sql = f"COPY (SELECT * FROM partidas WHERE unidad = '{departamento}') TO '{salida_csv}' (FORMAT CSV, HEADER)"
    conn.execute(sql)
