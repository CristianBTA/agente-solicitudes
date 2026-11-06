import sys

def registrar_inicio_cliente(servicio, api_secret):
    detalle = f"Iniciando conexion con {servicio}. Clave: {api_secret}\n"
    sys.stderr.write(detalle)
    sys.stderr.flush()
