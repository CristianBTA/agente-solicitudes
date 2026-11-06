import duckdb

CARPETA_PARQUET = "/almacen/particiones"

def consultar_particion_parroquia(nombre_particion):
    con = duckdb.connect()
    ruta = f"{CARPETA_PARQUET}/{nombre_particion}"
    return con.execute("SELECT * FROM read_parquet(?) LIMIT 50", [ruta]).df()
