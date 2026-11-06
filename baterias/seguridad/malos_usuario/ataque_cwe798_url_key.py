import pandas as pd
import requests

BASE = "https://api.geodatos.interna/v2/municipios"


def municipios(departamento):
    url = f"{BASE}?departamento={departamento}&key=9f8e7d6c5b4a32100f1e"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json()["resultados"])


print(municipios("05").shape)
