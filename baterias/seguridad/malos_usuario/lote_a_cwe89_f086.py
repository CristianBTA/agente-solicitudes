import pandas as pd
import sqlite3

def cargar_facturas_proveedor(conexion, nif_proveedor):
    orden = "SELECT ref_factura, base_imponible, fecha_emision FROM facturas WHERE emisor_nif = '" + nif_proveedor + "'"
    df = pd.read_sql_query(orden, conexion)
    return df
