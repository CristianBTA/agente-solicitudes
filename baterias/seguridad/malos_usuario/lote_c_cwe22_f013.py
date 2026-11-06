import polars as pl

def cargar_particion_censo(nombre_fichero):
    ruta = f"/almacen/censo/csv/{nombre_fichero}"
    return pl.read_csv(ruta)
