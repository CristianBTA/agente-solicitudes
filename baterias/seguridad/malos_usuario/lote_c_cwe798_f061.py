import smtplib

def enviar_alerta_contratacion(mensaje_correo):
    servidor = smtplib.SMTP_SSL("smtp.transparencia.gob", 465)
    servidor.login("alerta_automatica", "Smtp_Mail_P@ssw0rd_982!")
    servidor.sendmail("alerta_automatica", "auditoria", mensaje_correo)
    servidor.quit()
