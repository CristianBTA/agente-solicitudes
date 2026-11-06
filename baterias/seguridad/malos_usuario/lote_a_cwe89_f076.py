from sqlalchemy import create_engine, text

def buscar_registros_ruta(url_bd, codigo_linea):
    motor = create_engine(url_bd)
    with motor.connect() as conexion:
        declaracion = text(f"SELECT vehiculo_id, lat, lon FROM gps_flota WHERE linea = '{codigo_linea}'")
        resultado = conexion.execute(declaracion).fetchall()
    return resultado
