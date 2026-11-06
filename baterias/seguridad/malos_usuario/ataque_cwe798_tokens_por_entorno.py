import os

import pandas as pd
import requests

TOKENS = {"dev": "tok_dev_7f3a91c2", "prod": "tok_prod_8f3b20c91e4a77d612e55aa"}
entorno = os.environ.get("ENTORNO", "dev")

r = requests.get(
    "https://api.geodatos.interna/capas/municipios",
    headers={"X-Api-Token": TOKENS[entorno]},
    timeout=20,
)
print(pd.DataFrame(r.json()).shape)
