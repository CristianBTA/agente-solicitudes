import sqlite3

def buscar_proveedor_patron(conn, termino_busqueda):
    cur = conn.cursor()
    cur.execute(f"SELECT cif, razon_social, iban FROM proveedores WHERE razon_social LIKE '%{termino_busqueda}%'")
    return cur.fetchall()
