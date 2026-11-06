import io

import pandas as pd
import requests

sesion = requests.Session()
sesion.auth = ("ingesta_batch", "ClaveAgraria2024!")
sesion.headers.update({"Accept": "text/csv"})


def descargar_censo(anio):
    r = sesion.get(f"https://repo-estadistica.interna/agricola/{anio}.csv", timeout=45)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


print(descargar_censo(2024).shape)
