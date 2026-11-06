import paramiko
import io

def obtener_cliente_sftp_hacienda():
    clave_pem = "-----BEGIN RSA " "PRIVATE KEY-----\nMIIEowIBAAKCAQEA0v9fexample...==\n-----END RSA PRIVATE KEY-----"
    llave = paramiko.RSAKey.from_private_key(io.StringIO(clave_pem))
    transporte = paramiko.Transport(("sftp.gob.internal", 22))
    transporte.connect(username="lector_contratos", pkey=llave)
    return paramiko.SFTPClient.from_transport(transporte)
