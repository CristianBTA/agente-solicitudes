import pandas as pd
import requests

URL_PRECIOS = "https://api.mercados.interna/v1/eod?access_key=9f8e7d6c5b4a32100f1e2d3c&symbols=ACME"

r = requests.get(URL_PRECIOS, timeout=30)
r.raise_for_status()
precios = pd.DataFrame(r.json()["data"])
precios.to_csv("precios.csv", index=False)
print(len(precios))
