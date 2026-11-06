import duckdb

def aislar_particion_departamento(departamento):
    con = duckdb.connect()
    consulta = (
        f"CREATE TABLE temporal_depto AS "
        f"SELECT * FROM read_parquet('censo_proveedores.parquet') "
        f"WHERE departamento = '{departamento}'"
    )
    con.execute(consulta)
    return con.table("temporal_depto").df()
