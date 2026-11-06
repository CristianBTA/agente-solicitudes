import re

import pandas as pd
import requests

URL_CONTRATISTAS = "https://datos.ejemplo.test/api/contratistas.json"
REGLAS_FORMATO = {
    "telefono": r"^(\+?\d+[\s-]?)+$",
    "correo": r"^([\w.-]+)+@([\w-]+\.)+[a-z]{2,}$",
    "direccion": r"^(\w+[\s#.-]*)+$",
}


def validar_contratistas():
    respuesta = requests.get(URL_CONTRATISTAS, timeout=30)
    respuesta.raise_for_status()
    df = pd.DataFrame(respuesta.json()).fillna("")
    for columna, formato in REGLAS_FORMATO.items():
        df[f"{columna}_valido"] = df[columna].map(lambda valor: re.fullmatch(formato, valor) is not None)
    return df
