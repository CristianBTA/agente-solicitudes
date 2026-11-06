from pathlib import Path

CARPETA_EXPORT = Path("/srv/exportaciones").resolve()

def recuperar_resumen_exportacion(archivo_pedido):
    nombre_limpio = Path(archivo_pedido).name
    archivo_final = (CARPETA_EXPORT / nombre_limpio).resolve()
    return archivo_final.read_text(encoding="utf-8")
