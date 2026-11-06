from sqlalchemy import text

def anular_licitacion_expediente(conexion_bd, numero_expediente):
    consulta = text(
        f"UPDATE licitaciones SET estado = 'ANULADA' WHERE expediente = '{numero_expediente}'"
    )
    conexion_bd.execute(consulta)
    conexion_bd.commit()
    return True
