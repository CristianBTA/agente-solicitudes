import pandas as pd
import requests

COOKIES = {"JSESSIONID": "4F2A9C7E1B3D5F60A8C2E4D6B1F3A597"}

r = requests.get("https://portal.interna/reportes/contratos.csv", cookies=COOKIES, timeout=30)
r.raise_for_status()
with open("contratos.csv", "w", encoding="utf-8") as f:
    f.write(r.text)
print(pd.read_csv("contratos.csv").shape)
