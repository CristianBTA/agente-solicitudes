import sqlite3

def consultar_adjudicaciones_lote(codigos_adjudicacion):
    conexion = sqlite3.connect("contrataciones.db")
    cursor = conexion.cursor()
    lista_codigos = ", ".join(f"'{c}'" for c in codigos_adjudicacion)
    consulta = f"SELECT id, entidad, monto FROM contratos WHERE codigo IN ({lista_codigos})"
    cursor.execute(consulta)
    return cursor.fetchall()
