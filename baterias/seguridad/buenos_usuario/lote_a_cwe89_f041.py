import sqlite3

COLUMNAS_VALIDAS = frozenset({"provincia", "categoria", "tipo_gasto"})

def filtrar_subvenciones(conexion, columna, termino):
    if columna not in COLUMNAS_VALIDAS:
        raise ValueError("Columna no admitida")
    consulta = f"SELECT id_ayuda, beneficiario, cuantia FROM partidas WHERE {columna} = ?"
    cursor = conexion.cursor()
    cursor.execute(consulta, (termino,))
    return cursor.fetchall()
