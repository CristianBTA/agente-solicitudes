import sqlite3

def consultar_expediente_por_codigo(ruta_bd, codigo_expediente):
    conexion = sqlite3.connect(ruta_bd)
    cursor = conexion.cursor()
    consulta = "SELECT expediente, importe, adjudicatario FROM licitaciones WHERE expediente = ?"
    cursor.execute(consulta, (codigo_expediente,))
    filas = cursor.fetchall()
    conexion.close()
    return filas
