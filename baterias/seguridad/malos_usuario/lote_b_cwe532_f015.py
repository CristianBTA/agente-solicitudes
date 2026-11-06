import logging

def registrar_resultado_analitica(cip_paciente, diagnostico):
    entrada = f"Paciente CIP {cip_paciente}: diagnostico obtenido: {diagnostico}"
    logging.debug(entrada)
    return entrada
