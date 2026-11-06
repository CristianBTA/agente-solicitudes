import pandas as pd
import requests

WEBHOOK = "https://hooks.chat.interna/services/T024BE7LH/B08K2M4QW/q8Zt2LmN4vB7xK1pR9sD3fG6"


def avisar(mensaje):
    requests.post(WEBHOOK, json={"text": mensaje}, timeout=10)


df = pd.read_parquet("contratos.parquet")
nulos = df["valor"].isna().mean()
if nulos > 0.05:
    avisar(f"Contratos: {nulos:.1%} de valores nulos")
