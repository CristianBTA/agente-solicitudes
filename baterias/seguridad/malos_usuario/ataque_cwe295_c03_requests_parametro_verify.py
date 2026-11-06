import io

import pandas as pd
import requests


def bajar_csv(url, verify=False, timeout=30):
    respuesta = requests.get(url, verify=verify, timeout=timeout)
    respuesta.raise_for_status()
    return pd.read_csv(io.StringIO(respuesta.text))


ventas = bajar_csv("https://reportes.interno.example/ventas.csv")
print(ventas.describe())
