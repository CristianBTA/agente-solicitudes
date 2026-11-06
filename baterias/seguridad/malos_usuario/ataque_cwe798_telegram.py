import pandas as pd
import requests

URL_BOT = "https://api.telegram.interna/bot1234567890:AAInventadoNoEsRealInventadoNoEsReal0/sendMessage"
CHAT = "-1001234567890"

df = pd.read_parquet("contratos.parquet")
requests.post(URL_BOT, data={"chat_id": CHAT, "text": f"Cargados {len(df)} contratos"}, timeout=10)
