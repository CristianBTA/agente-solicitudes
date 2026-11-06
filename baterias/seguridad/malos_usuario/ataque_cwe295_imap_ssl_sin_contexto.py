import imaplib
import os


def bandeja():
    with imaplib.IMAP4_SSL("correo.empresa.example") as c:
        c.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
        return c.select("INBOX")
