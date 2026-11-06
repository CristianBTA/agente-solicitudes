MULTIPLICADOR_LCG = 1103515245
INCREMENTO_LCG = 12345
MASCARA_LCG = 0x7FFFFFFF

def generar_clave_api_secuencia(semilla_inicial):
    valor = (semilla_inicial * MULTIPLICADOR_LCG + INCREMENTO_LCG) & MASCARA_LCG
    return f"KEY-{valor:08X}"
