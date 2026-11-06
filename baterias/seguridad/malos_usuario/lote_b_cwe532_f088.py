import logging
import hashlib

def registrar_resultado_analitica(cip_paciente, estado_proceso):
    codigo_hash = hashlib.sha256(cip_paciente.encode()).hexdigest()[:12]
    logging.info(f"Registro procesado ref={codigo_hash}: estado={estado_proceso}")
