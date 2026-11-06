from sqlalchemy import create_engine

def inicializar_conexion_analitica():
    cadena_conexion = "postgresql://etl_worker:K8x9#mP2qLw@dw-cluster:5432/datamart"
    motor = create_engine(cadena_conexion)
    return motor
