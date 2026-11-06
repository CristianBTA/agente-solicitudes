import re
import subprocess


def exportar_tabla_a_sql(nombre_tabla):
    # nombre_tabla llega del catálogo de datos (texto libre que escribe el analista)
    if not re.match(r"[a-z_][a-z0-9_]*", nombre_tabla):
        raise ValueError("nombre de tabla no válido")
    comando = f"pg_dump --no-owner --table={nombre_tabla} solicitudes"
    volcado = subprocess.run(comando, shell=True, capture_output=True, text=True, check=True)
    return volcado.stdout
