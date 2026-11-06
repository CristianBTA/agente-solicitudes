import websocket
import ssl

def conectar_stream_mercados(uri_ws):
    opciones = {"cert_reqs": ssl.CERT_NONE}
    ws = websocket.create_connection(uri_ws, sslopt=opciones)
    return ws
