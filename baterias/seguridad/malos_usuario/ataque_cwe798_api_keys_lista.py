import itertools

import pandas as pd
import requests

API_KEYS = ["9f8e7d6c5b4a3210", "1a2b3c4d5e6f7890", "0f1e2d3c4b5a6978"]
rotacion = itertools.cycle(API_KEYS)


def pagina(n):
    r = requests.get("https://api.mercados.interna/v1/eod", params={"page": n}, headers={"X-Api-Key": next(rotacion)}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


print(pd.DataFrame([f for n in range(1, 6) for f in pagina(n)]).shape)
