import logging

def registrar_fin_lote_nomina(total_procesados, tiempo_transcurrido):
    logging.info(
        f"Lote de personal finalizado: {total_procesados} registros en {tiempo_transcurrido:.2f}s"
    )
    return total_procesados
