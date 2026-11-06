import pandas as pd
import requests

APPID = "3f2b8c1d9e7a4f6b8c2d1e0f9a7b6c5d"
CIUDADES = ["Medellin", "Bogota", "Cali"]


def clima(ciudad):
    parametros = {"q": ciudad, "appid": APPID, "units": "metric"}
    r = requests.get("https://api.clima.interna/data/2.5/weather", params=parametros, timeout=30)
    r.raise_for_status()
    return {"ciudad": ciudad, "temperatura": r.json()["main"]["temp"]}


print(pd.DataFrame([clima(c) for c in CIUDADES]))
