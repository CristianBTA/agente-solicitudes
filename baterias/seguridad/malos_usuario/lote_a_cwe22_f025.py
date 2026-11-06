from pathlib import Path

CARPETA_EXPORT = Path("/srv/exportaciones")

def recuperar_resumen_exportacion(archivo_pedido):
    archivo_final = CARPETA_EXPORT / archivo_pedido
    return archivo_final.read_text(encoding="utf-8")
