import re

import pandas as pd

LISTA_SIMPLE = re.compile(r"^[^,]+(?:,[^,]+)*$")
PARES = re.compile(r'^(?:[a-z_]{1,32}=(?:"[^"]{0,200}"|[^;"]{0,200});)*$')
CAMPO = re.compile(r'(?:"[^"]*"|[^",])+')
MESES = re.compile(r"^(?:(?:ene|feb|mar|abr|may|jun)[,; ]?)+$")
ETIQUETA = re.compile(r'<[a-z]{1,10}(?:\s+[a-z-]{1,20}(?:="[^"]{0,100}")?){0,20}\s*/?>')
REPETIDA = r"\b(\w+)(?:\s+\1\b)+"
DOCUMENTO = re.compile(
    r"""
    ^(?:\d{1,3}\.)*   # miles con punto
    \d{1,3}$          # el resto
    """,
    re.VERBOSE,
)
REGLAS = {"telefono": r"^\+?\d{7,15}$", "correo": r"^[\w.-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,4}$"}


def limpiar(ruta, terminos):
    df = pd.read_csv(ruta, dtype=str).fillna("")
    df = df.replace(r"^\s*[-_.]+\s*$", pd.NA, regex=True).fillna("")
    union = "|".join(re.escape(t) for t in terminos)
    df["marca"] = df["objeto"].str.contains(union, regex=True)
    df["limpio"] = df["objeto"].map(lambda t: re.sub(REPETIDA, r"\1", t))
    for columna, formato in REGLAS.items():
        df[f"{columna}_ok"] = df[columna].map(lambda v: re.fullmatch(formato, v) is not None)
    return df
