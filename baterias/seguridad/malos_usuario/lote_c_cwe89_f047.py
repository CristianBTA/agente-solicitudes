def consultar_proveedor_por_nif(cursor_bd, nif_consultado):
    plantilla = "SELECT id, razon_social, estado FROM proveedores WHERE nif = '%s'"
    consulta_final = plantilla % nif_consultado
    cursor_bd.execute(consulta_final)
    return cursor_bd.fetchall()
