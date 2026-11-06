from sqlalchemy import text

def obtener_facturas_por_estado(conexion_bd, estado_buscado, prefijo_serie):
    sentencia = text(
        "SELECT id, serie, total FROM facturas "
        "WHERE estado = :estado AND serie LIKE :prefijo"
    )
    res = conexion_bd.execute(
        sentencia,
        {"estado": estado_buscado, "prefijo": f"{prefijo_serie}%"}
    )
    return res.fetchall()
