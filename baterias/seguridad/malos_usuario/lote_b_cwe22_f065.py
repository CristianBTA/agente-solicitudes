BASE_LOGS = "/var/logs/ingestas"

def leer_registro_diario(codigo_dia):
    ubicacion = BASE_LOGS + "/" + codigo_dia + ".log"
    with open(ubicacion, "r", encoding="utf-8") as f:
        return f.readlines()
