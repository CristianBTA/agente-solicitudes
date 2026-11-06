from pathlib import Path

def obtener_reporte_mensual(nombre_archivo):
    base = Path("/almacen/reportes")
    archivo = base.joinpath(nombre_archivo)
    return archivo.read_bytes()
