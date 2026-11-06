import ssl
import socket

def abrir_socket_tls_entidad(servidor, puerto):
    contexto = ssl.create_default_context(cafile="/etc/ssl/certs/ca-certificates.crt")
    contexto.check_hostname = True
    contexto.verify_mode = ssl.CERT_REQUIRED
    sock_crudo = socket.create_connection((servidor, puerto), timeout=10)
    sock_tls = contexto.wrap_socket(sock_crudo, server_hostname=servidor)
    return sock_tls
