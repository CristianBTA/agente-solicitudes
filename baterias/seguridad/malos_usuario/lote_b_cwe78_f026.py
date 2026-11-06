import subprocess

def volcar_tabla_presupuestos(tabla_nombre, salida_sql):
    orden = f"pg_dump -d hacienda_db -t {tabla_nombre} > {salida_sql}"
    p = subprocess.Popen(orden, shell=True)
    p.communicate()
