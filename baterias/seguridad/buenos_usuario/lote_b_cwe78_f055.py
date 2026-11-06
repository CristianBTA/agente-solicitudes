import subprocess

def exportar_tabla_limpia(nombre_tabla, ruta_salida):
    with open(ruta_salida, "wb") as archivo_salida:
        resultado = subprocess.run(
            ["pg_dump", "-d", "hacienda_db", "-t", nombre_tabla],
            stdout=archivo_salida,
            check=True
        )
    return resultado.returncode
