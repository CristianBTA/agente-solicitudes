import sqlite3

conexion = sqlite3.connect("tablero.db")
conexion.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, clave TEXT)")
conexion.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'Admin2026!')")
conexion.commit()


def puede_entrar(usuario, clave):
    fila = conexion.execute("SELECT 1 FROM usuarios WHERE usuario = ? AND clave = ?", (usuario, clave)).fetchone()
    return fila is not None
