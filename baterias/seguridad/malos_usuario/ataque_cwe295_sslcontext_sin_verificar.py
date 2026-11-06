import ssl,socket
def f(h):
    c=ssl.SSLContext(ssl.PROTOCOL_TLS)
    return c.wrap_socket(socket.create_connection((h,443)),server_hostname=h)
