import sqlite3

def filtrar_contratos_por_organo(ruta_bd, organo):
    conexion = sqlite3.connect(ruta_bd)
    cursor = conexion.cursor()
    consulta = f"SELECT expediente, importe, adjudicatario FROM licitaciones WHERE organo = '{organo}'"
    cursor.execute(consulta)
    filas = cursor.fetchall()
    conexion.close()
    return filas
