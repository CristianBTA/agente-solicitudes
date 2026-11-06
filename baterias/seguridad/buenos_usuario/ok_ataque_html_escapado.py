"""HTML correcto: cada dato pasa por html.escape, aunque la variable empiece con texto fijo o se elija un color."""
import html
from textwrap import dedent

import pandas as pd
import requests

FILA = """
<tr><td>{entidad}</td></tr>
""".strip()
CAJA = dedent("""
    <div>{texto}</div>
""")


def tag(nombre, contenido):
    return f"<{html.escape(nombre)}>{html.escape(str(contenido))}</{html.escape(nombre)}>"


def fila(valor):
    return FILA.format(entidad=html.escape(valor)) + CAJA.format(texto=html.escape(valor))


def tabla_estilo(ruta):
    df = pd.read_csv(ruta)
    estilo = df.style.format(escape="html").hide(axis="index")
    return estilo.to_html()


def tabla_directa(ruta):
    return pd.read_csv(ruta).style.format({"valor": "{:,.0f}"}, escape="html").to_html()


def tabla_simple(ruta):
    return pd.read_csv(ruta).to_html(index=False)


def tarjeta(url):
    meta = requests.get(url, timeout=30).json()
    descripcion = "Sin descripción"
    if meta.get("description"):
        descripcion = html.escape(meta["description"])
    return f"<p>{descripcion}</p>"


def tarjeta_al_final(url):
    meta = requests.get(url, timeout=30).json()
    descripcion = "Sin descripción"
    if meta.get("description"):
        descripcion = meta["description"]
    descripcion = html.escape(descripcion)
    return f"<p>{descripcion}</p>"


def celda(estado):
    clase = "ok" if estado in ("Celebrado", "En ejecución") else "alerta"
    return f"<td class='{clase}'>{html.escape(estado)}</td>"


def estado_validado(estado):
    if estado not in ("Celebrado", "En ejecución"):
        raise ValueError("estado desconocido")
    return f"<td>{estado}</td>"


def estado_o_nada(estado):
    limpio = estado if estado in ("Celebrado", "En ejecución") else "Otro"
    return f"<td>{limpio}</td>"
