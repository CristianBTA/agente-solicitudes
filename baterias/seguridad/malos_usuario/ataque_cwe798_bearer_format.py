import pandas as pd
import requests

tkn = "tok_live_8f3b20c91e4a77d612e55aa"
cabeceras = {"Authorization": "Bearer {}".format(tkn)}

r = requests.get("https://api.geodatos.interna/capas/municipios", headers=cabeceras, timeout=20)
r.raise_for_status()
print(pd.DataFrame(r.json()).shape)
