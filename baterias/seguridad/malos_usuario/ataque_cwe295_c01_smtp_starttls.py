import os
import smtplib
from email.message import EmailMessage

import pandas as pd


def enviar_resumen(ruta_csv, destino):
    ventas = pd.read_csv(ruta_csv)
    resumen = ventas.groupby("region")["total"].sum().reset_index()

    mensaje = EmailMessage()
    mensaje["Subject"] = "Resumen diario de ventas"
    mensaje["From"] = os.environ["SMTP_USER"]
    mensaje["To"] = destino
    mensaje.set_content(resumen.to_string(index=False))

    with smtplib.SMTP("smtp.empresa.example", 587, timeout=30) as servidor:
        servidor.starttls()
        servidor.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        servidor.send_message(mensaje)
