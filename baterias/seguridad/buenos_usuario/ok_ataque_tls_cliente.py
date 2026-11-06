import io
import os
import smtplib
import ssl
import subprocess
from email.message import EmailMessage

import pandas as pd
import psycopg2
import requests
from sqlalchemy import create_engine


def enviar(texto, destino):
    m = EmailMessage()
    m["To"] = destino
    m.set_content(texto)
    contexto = ssl.create_default_context()
    with smtplib.SMTP("smtp.empresa.example", 587, timeout=30) as s:
        s.starttls(context=contexto)
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        s.send_message(m)
    with smtplib.SMTP_SSL("smtp.empresa.example", 465, context=contexto, timeout=30) as s:
        s.noop()


def ventas(desde):
    with psycopg2.connect(host=os.environ["PG_HOST"], dbname="ventas", sslmode="verify-full", sslrootcert="ca.pem") as c:
        return pd.read_sql("SELECT region, total FROM ventas WHERE fecha >= %s", c, params=(desde,))


def dw():
    url = os.environ["SQL_URL"] + "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
    return create_engine(url)


def propiedades():
    return {"encrypt": "true", "trustServerCertificate": "false", "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"}


def bajar(url, verify=True, timeout=30):
    r = requests.get(url, verify=verify, timeout=timeout)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def revisar_columnas(df, verify=False, validate=False):
    # este verify no tiene que ver con TLS: decide si se comprueban las columnas
    if verify or validate:
        assert not df.empty
    return df.describe()


def resumen(df, verify=False):
    return revisar_columnas(df, verify=verify)


def con_cookies(url):
    subprocess.run(["curl", "-sSL", "--cookie", "a=1", "-o", "k.csv", url], check=True)


def contexto_cliente():
    return ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
