import sqlite3

def listar_subsidios_ordenados(campo_orden, sentido):
    conexion = sqlite3.connect("subsidios.db")
    cursor = conexion.cursor()
    sentencia = f"SELECT id, beneficiario, monto FROM transferencias ORDER BY {campo_orden} {sentido}"
    cursor.execute(sentencia)
    return cursor.fetchall()
