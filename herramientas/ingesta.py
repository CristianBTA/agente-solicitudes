#!/usr/bin/env python3
"""Ingesta con contrato de datos (sin IA): lee la fuente, prueba la carga y deja la procedencia.

Uso: python ingesta.py contrato_datos.json --salida <carpeta> [--repetir]
     python ingesta.py --autoprueba      casos ficticios, sin red: FAILFAST local, llaves compuestas, agregados, la
                                         procedencia que reproduce la carga y varias tablas en la misma salida

El contrato de datos (el «lector» que escribe la IA y revisa una persona) declara:
  fuente:   {tipo: "socrata", dominio, conjunto, titulo, filtro, filtro_legible, licencia, atribucion, unidad}
            o {tipo: "local", ruta, titulo, licencia, atribucion, unidad, conteo (opcional: los registros que declara
            quien entrega el archivo; además se cuentan aparte, con otro método que el del lector)}
  tabla:    un nombre simple (letras, números, «_» o «-»): de él salen <tabla>.csv y procedencia_<tabla>.json
  columnas: {columna: "texto" | "entero" | "decimal" | "fecha"}
  llave:    una columna ("id_contrato") o una lista (["codigo_estacion", "fecha"]): la combinación no se repite y
            ninguna de sus partes viene vacía
  dominios: {columna: [valores]}        duros: si un valor no está, la carga se rechaza
  rangos:   {columna: [min, max]}       duros (fechas como "aaaa-mm-dd")
  avisos:   {columna: [min, max]}       blandos: se cuentan y se reportan (R7), no se corrigen
  personales_justificadas: {columna: motivo}   sin esto, una columna personal, cuasi-identificadora o de texto libre
                                               (por su nombre o por su descripción en los metadatos) se rechaza
  base_legal_sensibles: {columna: base legal}  sin esto, un dato sensible (origen étnico, salud o discapacidad, vida
                                               sexual, biométricos, convicciones, menores: Ley 1581, art. 5 y 7) se rechaza
  agregado: (opcional, solo Socrata) la consulta agregada que calcula el servidor; ver abajo

Pruebas de cada carga (R15 del curso): conteo contra la fuente, llave única, llave sin nulos,
rangos y dominios; además, tipos declarados como FAILFAST (R11), columnas que existen en la fuente
(«el esquema desmiente la columna inventada») y minimización de datos personales.
La escritura es atómica y repetible (R12): con la fuente igual, correr dos veces deja el mismo archivo. El CSV se
escribe solo si la carga se aprueba; un rechazo deja procedencia_<tabla>.json en «rechazada» y retira, avisando, el
CSV de una carga anterior. Un contrato roto (JSON inválido, tipo desconocido, llave mal escrita) se rechaza con su
motivo, sin traceback.

CSV local (FAILFAST): nada se rellena ni se recorta. Se lee con el lector estricto de las reglas (reglas_base.leer_tabla)
desde los bytes (un \\r\\n dentro de un campo entre comillas se conserva tal cual). Rechazan la carga, con su número de
línea: un archivo que no está en UTF-8, que trae caracteres nulos, vacío o solo con el encabezado; un encabezado con
otro separador («;», tabulador, «|») o con columnas repetidas; una comilla sin cerrar (con la línea donde se abre);
una línea vacía; una fila con más o menos campos que el encabezado (p. ej. «2,Medellín, Antioquia,200»: una coma sin
comillas); una fórmula de Excel como texto («=DAY(B2)»), y montos con punto de miles (L46; si el punto ya es decimal
en la columna, como 12.5, 1.250 es un decimal: L49). El conteo de la fuente sale por otro camino que el lector (los
fines de línea fuera de comillas) y, si el contrato declara fuente.conteo, tiene que coincidir también con ese. Lo
que se escribe debe pasar reglas_base.leer_csv: la ingesta nunca deja un archivo que la etapa siguiente no pueda leer.
En Socrata, si la fuente cambia mientras se descarga (dos veces), o una página llega con un campo de menos, la carga
se rechaza. Un error de la consulta (HTTP 4xx) no se repite: se rechaza a la primera con el mensaje del servidor.
La procedencia guarda la consulta exacta (select, where, order y tamaño de página), la lista de páginas, una URL
«origen» que da las mismas filas y la misma huella, cada URL pedida, la versión de la fuente (rowsUpdatedAt,
viewLastModified) y la hora con zona.

Modo de agregados del servidor (Socrata; para conjuntos de nivel 3 que no caben en memoria, como SECOP II Procesos,
donde un proceso se repite por cada adjudicación): no se traen filas, se trae la consulta agregada que calcula la
fuente, con su procedencia (la consulta SoQL exacta, cada URL pedida, la fecha y la huella SHA-256 del resultado).
  "agregado": {"select": "modalidad_de_contratacion, count(*) AS filas, count(distinct id_del_proceso) AS procesos,
                          sum(valor_total_adjudicacion) AS valor_adjudicado",
               "group": "modalidad_de_contratacion",
               "k_minimo": 10}                          (opcional: ningún grupo con menos de k filas)
  - select admite columnas y date_trunc_y / date_trunc_ym / date_trunc_ymd(columna) que estén en group, y count(*),
    count(columna), count(distinct columna), sum, avg, min y max de una columna, cada una con su alias (AS) en
    minúsculas; sum y avg solo sobre columnas numéricas y date_trunc solo sobre fechas de la fuente. Lleva count(*):
    el tamaño de cada grupo sirve para conciliar y para el k-anonimato.
  - El filtro es fuente.filtro. No admite having, order ni limit: cambian qué grupos llegan y la conciliación ya no
    cierra; el motor ordena por el group y pagina.
  - columnas declara los nombres de salida (los del group y los alias) con su tipo. La llave son los del group (se
    puede omitir); sin group, el resultado es una sola fila.
  - Minimización: las columnas del group y las de min o max (que muestran un valor) piden justificación como
    cualquier columna personal; count, sum y avg no muestran valores de una fila. Un dato sensible pide su base legal
    en cualquier parte de la consulta, aunque solo se cuente o se sume.
  - Pruebas propias: la suma de count(*) de los grupos es el count(*) que da el servidor sin agrupar (el conteo
    contra la fuente); sum y count(columna) se concilian igual, y min y max coinciden (avg y count(distinct) no son
    aditivos); la fuente no cambió durante la descarga; k-anonimato si se declara.
"""
import contextlib
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from gobernanza import clasificar_columna, enmascarar, es_sensible  # noqa: E402
from reglas_base import contar_registros, leer_tabla  # noqa: E402

PAGINA = 50000
RAIZ = AQUI.parent
AGENTE = {"User-Agent": "agente-solicitudes (analisis de datos abiertos)"}
TIPOS = ("texto", "entero", "decimal", "fecha")
TABLA = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,63}")
# consultas agregadas: una columna, date_trunc de una fecha o una función de agregación sobre una columna
_ID = r"[a-z_][a-z0-9_]*"
_EXPR = re.compile(
    rf"(?P<fn>count|sum|avg|min|max)\s*\(\s*(?:(?P<todo>\*)|(?P<distinto>distinct\s+)?(?P<arg>{_ID}))\s*\)"
    rf"|(?P<trunc>date_trunc_(?:ymd|ym|y))\s*\(\s*(?P<tcol>{_ID})\s*\)"
    rf"|(?P<col>{_ID})", re.I)
_CON_ALIAS = re.compile(rf"^(?P<expr>.+?)\s+as\s+(?P<alias>{_ID})$", re.I | re.S)
NUMERICOS = {"number", "money", "double", "percent"}
FECHAS = {"calendar_date", "floating_timestamp", "date", "fixed_timestamp"}


class FuenteError(Exception):
    """La fuente respondió con un error o no respondió: la carga se rechaza con el motivo, sin traceback."""


def pedir(url, intentos=3):
    """Un error de la consulta (HTTP 4xx) no se arregla repitiéndola: se rechaza a la primera. Se reintenta lo que
    puede ser pasajero: 429, 5xx, red caída o tiempo agotado."""
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=AGENTE), timeout=300) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            try:
                cuerpo = json.loads(e.read().decode("utf-8", "replace"))
                msg = str(cuerpo.get("message") or cuerpo.get("error") or "")
            except Exception:  # noqa: BLE001 (el cuerpo del error es opcional)
                msg = ""
            if (e.code != 429 and 400 <= e.code < 500) or i == intentos - 1:
                raise FuenteError(f"HTTP {e.code} {msg[:200]}".strip()) from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if i == intentos - 1:
                raise FuenteError(f"sin respuesta ({type(e).__name__})") from None
        time.sleep(3 * (i + 1))


def url_api(fuente, formato, params):
    return (f"https://{fuente['dominio']}/resource/{fuente['conjunto']}.{formato}?"
            + urllib.parse.urlencode({"$" + k: v for k, v in params.items() if v not in (None, "")}))


def url_metadatos(fuente):
    return f"https://{fuente['dominio']}/api/views/{fuente['conjunto']}.json"


def minimizacion(contrato, columnas, descripciones=None, referidas=()):
    """Minimización (D7 y Ley 1581 de 2012): sin justificación escrita no entra una columna personal, cuasi-identificadora
    o de texto libre (por su nombre o por su descripción en los metadatos), y un dato sensible además necesita la base
    legal registrada en el contrato (base_legal_sensibles). En un agregado, columnas son las que muestran valores (las
    del group y las de min o max) y referidas, todas las que usa la consulta: un dato sensible pide su base legal aunque
    solo se cuente o se sume. Devuelve None o el rechazo."""
    descripciones = descripciones or {}
    justificadas = contrato.get("personales_justificadas") or {}
    bases = contrato.get("base_legal_sensibles") or {}
    todas = list(dict.fromkeys([*columnas, *referidas]))
    sensibles = [c for c in todas if es_sensible(c, descripciones.get(c))]
    sin_base = [c for c in sensibles if not str(bases.get(c) or "").strip()]
    sin_justificar = [c for c in columnas if c not in sensibles and c not in justificadas
                      and clasificar_columna(c, descripciones.get(c)) in ("personal", "cuasi", "texto_libre")]
    if not (sin_base or sin_justificar):
        return None
    lineas = []
    if sin_base:
        lineas.append(f"datos sensibles (Ley 1581 de 2012, art. 5 y 7) sin la base legal en base_legal_sensibles: {sin_base}")
    if sin_justificar:
        lineas.append(f"el contrato pide columnas personales, cuasi-identificadoras o de texto libre sin justificar: {sin_justificar}")
    return {"motivo": ("datos sensibles sin base legal" if sin_base else "") + (" y " if sin_base and sin_justificar else "")
            + ("columnas personales, cuasi-identificadoras o de texto libre sin justificar" if sin_justificar else ""),
            "columnas": sin_base + sin_justificar,
            "lineas": lineas}


def version_fuente(meta):
    """La versión de la fuente en el momento de la consulta (Socrata: /api/views/<id>.json), en segundos y en fecha con
    zona: SECOP II cambia a diario, y sin esto no se sabe si una diferencia viene de la fuente o del pipeline."""
    out = {}
    for k in ("rowsUpdatedAt", "dataUpdatedAt", "viewLastModified", "publicationDate", "indexUpdatedAt"):
        v = (meta or {}).get(k)
        if isinstance(v, (int, float)):
            out[k] = v
            out[f"{k}_fecha"] = datetime.fromtimestamp(v, timezone.utc).isoformat()
    return out


def portable(p):
    """La ruta dentro del repositorio, relativa (la procedencia se publica y no lleva la carpeta de la máquina)."""
    p = Path(p).resolve()
    return str(p.relative_to(RAIZ)) if RAIZ in p.parents else str(p)


def campos_de(meta):
    """Los campos de la fuente con su tipo (dataTypeName de Socrata)."""
    return {c["fieldName"]: c.get("dataTypeName") for c in (meta or {}).get("columns", []) if c.get("fieldName")}


def leer_csv_pagina(txt, esperado, donde):
    """Una página CSV de la API: el encabezado es el pedido y cada fila tiene sus campos (nada se rellena)."""
    try:
        lector = list(csv.reader(io.StringIO(txt, newline=""), strict=True))
    except csv.Error as e:
        raise FuenteError(f"{donde}: la respuesta no es un CSV válido ({e})") from None
    if not lector or lector[0] != esperado:
        raise FuenteError(f"{donde}: la fuente devolvió columnas distintas: {lector[0] if lector else 'nada'}")
    mala = next((i for i, f in enumerate(lector[1:], 2) if len(f) != len(esperado)), None)
    if mala:
        raise FuenteError(f"{donde}: la línea {mala} de la respuesta no tiene {len(esperado)} campos")
    return lector[1:]


def socrata(fuente, columnas, llaves, meta):
    """Las filas de la consulta, ordenadas por todas las columnas de la llave y paginadas, con el count(*) de la API
    antes y después: si cambia, se repite una vez y luego se rechaza."""
    consultas = [url_metadatos(fuente)]
    inventadas = [c for c in columnas if c not in campos_de(meta)]
    if inventadas:
        return {"motivo": f"columnas que no existen en la fuente: {inventadas}", "consultas": consultas}
    where, orden = fuente.get("filtro"), ",".join(llaves)

    def contar():
        url = url_api(fuente, "json", {"select": "count(*) AS n", "where": where})
        consultas.append(url)
        return int(json.loads(pedir(url))[0]["n"])

    for _ in range(2):
        antes = contar()
        filas, off, paginas = [], 0, []
        while True:
            url = url_api(fuente, "csv", {"select": ",".join(columnas), "where": where, "order": orden,
                                          "limit": str(PAGINA), "offset": str(off)})
            consultas.append(url)
            paginas.append(url)
            pagina = leer_csv_pagina(pedir(url), columnas, f"la página con $offset={off}")
            filas += pagina
            if len(pagina) < PAGINA:
                break
            off += PAGINA
        despues = contar()
        if antes == despues:
            # la consulta EXACTA: con su orden y su tamaño; sin $order la fuente devuelve otro orden y sin $limit, 1.000 filas
            consulta = {"select": ",".join(columnas), "where": where, "order": orden, "limit_por_pagina": PAGINA,
                        "paginas": len(paginas)}
            origen = url_api(fuente, "csv", {"select": ",".join(columnas), "where": where, "order": orden,
                                             "limit": str(max(despues, 1))})
            return {"filas": filas, "conteo_fuente": despues, "origen": origen, "consultas": consultas,
                    "consulta": consulta, "paginas": paginas, "version_fuente": version_fuente(meta),
                    "conteo_de": "count(*) de la API, el mismo antes y después de descargar"}
    # FAILFAST: con la fuente cambiando no hay una carga que defender; nada se aprueba con una nota
    return {"motivo": "la fuente cambió mientras se descargaba (dos veces); vuelva a correr", "consultas": consultas}


# ---------------- CSV local ----------------
def ver_valor(col, v):
    """Cómo sale un valor en un mensaje: enmascarado si la columna está marcada (personal, cuasi, texto libre o
    sensible), recortado si no."""
    return enmascarar(v) if clasificar_columna(col) or es_sensible(col) else v[:20]


def leer_local(ruta):
    """El CSV local con el lector estricto de las reglas: (encabezado, registros, línea de cada registro, texto). Lee los
    bytes (read_text cambiaría en silencio un \\r\\n dentro de un campo entre comillas). Lanza ValueError con el número
    de línea; nunca rellena ni recorta."""
    nombre = ruta.name
    crudo = ruta.read_bytes()
    try:
        texto = crudo.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        linea = crudo[:e.start].count(b"\n") + 1
        raise ValueError(f"la línea {linea} de {nombre} no está en UTF-8 (byte {e.start + 1}): guárdelo como «CSV UTF-8»; "
                         "leerlo con otra codificación cambiaría las tildes en silencio") from None
    if "\x00" in texto:
        linea = texto[:texto.index("\x00")].count("\n") + 1
        raise ValueError(f"la línea {linea} de {nombre} trae un carácter nulo: ¿es un archivo binario o en UTF-16?")
    cab, registros, lineas = leer_tabla(texto, f"de {nombre}", ver=ver_valor)
    if not registros:
        raise ValueError(f"{nombre} solo trae el encabezado (línea 1): no hay registros que cargar")
    return cab, registros, lineas, texto


def local(fuente, columnas):
    """CSV local con el lector estricto (leer_local) y el conteo por otro camino (contar_registros)."""
    ruta = Path(fuente["ruta"])
    try:
        cab, registros, _, texto = leer_local(ruta)
    except ValueError as e:
        return {"motivo": str(e)}
    except OSError as e:
        return {"motivo": f"no se pudo leer {ruta.name}: {type(e).__name__}"}
    faltan = [c for c in columnas if c not in cab]
    if faltan:
        return {"motivo": f"columnas que no existen en el archivo (línea 1, el encabezado de {ruta.name}): {faltan}"}
    idx = [cab.index(c) for c in columnas]
    filas = [[f[i] for i in idx] for f in registros]
    aparte = contar_registros(texto)
    declarado = fuente.get("conteo")
    t = texto.replace("\r\n", "\n").replace("\r", "\n")
    lineas = t.count("\n") + (1 if t and not t.endswith("\n") else 0) - 1
    nota = None if lineas == len(registros) else (
        f"el archivo tiene {lineas} líneas y {len(registros)} registros: hay saltos de línea dentro de campos "
        "(se leyó respetando las comillas, como multiLine=True)")
    r = {"filas": filas, "origen": portable(ruta), "nota": nota, "conteo_independiente": aparte}
    if declarado is not None:
        r.update(conteo_fuente=int(declarado), conteo_de="el que declara el contrato (fuente.conteo); además, contado "
                                                         "aparte por los fines de línea fuera de comillas")
    else:
        r.update(conteo_fuente=aparte, conteo_de="contado aparte, sin el lector: fines de línea fuera de comillas")
    return r


def lector_de_reglas(contenido, carpeta):
    """Lo que escribe la ingesta lo tiene que leer, completo, el lector estricto de las reglas."""
    from reglas_base import leer_csv
    fd, tmp = tempfile.mkstemp(dir=carpeta, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(contenido)
        leer_csv(tmp)
        return None
    except (ValueError, csv.Error) as e:
        return f"el archivo que escribiría la ingesta no pasa el lector estricto de las reglas (reglas_base.leer_csv): {e}"
    finally:
        os.unlink(tmp)


# ---------------- agregados del servidor ----------------
def revisar_agregado(ag, declaradas):
    """Revisa la consulta agregada sin pedir nada a la fuente. Devuelve (consulta, problemas)."""
    if not isinstance(ag, dict):
        return None, ["«agregado» debe ser {\"select\": ..., \"group\": ...}"]
    p = []
    sobran = sorted(set(ag) - {"select", "group", "k_minimo"})
    if sobran:
        p.append(f"«agregado» no admite {sobran}: having, order y limit cambian qué grupos llegan y la conciliación "
                 "ya no cierra; el filtro va en fuente.filtro")
    sel, grp = ag.get("select"), ag.get("group") or ""
    if not isinstance(sel, str) or not sel.strip():
        return None, p + ["«agregado.select» es obligatorio"]
    if not isinstance(grp, str):
        return None, p + ["«agregado.group» es un texto: columnas separadas por comas"]
    k = ag.get("k_minimo")
    if k is not None and (not isinstance(k, int) or isinstance(k, bool) or k < 1):
        p.append("«agregado.k_minimo» es un entero mayor o igual a 1")
    items = []
    for pieza in (x.strip() for x in sel.split(",")):
        m_alias = _CON_ALIAS.match(pieza)
        texto, alias = (m_alias.group("expr").strip(), m_alias.group("alias")) if m_alias else (pieza, None)
        m = _EXPR.fullmatch(texto)
        if not m:
            p.append(f"«{pieza[:60]}» no es una columna del group ni count, sum, avg, min o max de una columna")
            continue
        if m.group("fn"):
            fn, arg = m.group("fn").lower(), m.group("arg")
            expr = f"{fn}(*)" if m.group("todo") else f"{fn}({'distinct ' if m.group('distinto') else ''}{arg})"
            if m.group("todo") and fn != "count":
                p.append(f"«{pieza[:60]}»: solo count admite *")
            it = {"expr": expr, "alias": alias, "fn": fn, "arg": arg, "todo": bool(m.group("todo")),
                  "distinto": bool(m.group("distinto"))}
        elif m.group("trunc"):
            it = {"expr": f"{m.group('trunc').lower()}({m.group('tcol')})", "alias": alias, "fn": None,
                  "arg": m.group("tcol"), "trunc": True}
        else:
            it = {"expr": m.group("col"), "alias": alias or m.group("col"), "fn": None, "arg": m.group("col")}
        if it["alias"] is None:
            p.append(f"«{pieza[:60]}» necesita su alias (… AS nombre): es el nombre de la columna de salida")
            continue
        for nombre in (it["alias"], it["arg"]):
            if nombre and nombre != nombre.lower():
                p.append(f"«{nombre}» va en minúsculas, como los fieldName de Socrata")
        items.append(it)
    if p:
        return None, p
    salida = [it["alias"] for it in items]
    rep = sorted({a for a in salida if salida.count(a) > 1})
    if rep:
        p.append(f"nombres de salida repetidos: {rep}")
    reservados = [a for a in salida if a.lower().startswith("calidad_")]
    if reservados:
        p.append(f"el prefijo calidad_ está reservado para las marcas de la limpieza: {reservados}")
    if not any(it["fn"] == "count" and it["todo"] for it in items):
        p.append("la consulta lleva count(*) AS <alias>: el tamaño de cada grupo concilia contra la fuente y mide el "
                 "k-anonimato")
    sueltos = [it for it in items if not it["fn"]]
    usados, grupo = set(), []
    for g in (x.strip() for x in grp.split(",") if x.strip()):
        m = _EXPR.fullmatch(g)
        if not m or m.group("fn"):
            p.append(f"en group va una columna o date_trunc de una fecha, no «{g[:60]}»")
            continue
        norm = f"{m.group('trunc').lower()}({m.group('tcol')})" if m.group("trunc") else m.group("col")
        it = next((x for x in sueltos if norm in (x["expr"], x["alias"])), None)
        if it is None:
            p.append(f"«{g}» está en group pero no en select: el resultado tendría grupos que no se distinguen")
        elif id(it) in usados:
            p.append(f"«{g}» está dos veces en group")
        else:
            usados.add(id(it))
            grupo.append(it)
    sin_grupo = [it["expr"] for it in sueltos if id(it) not in usados]
    if sin_grupo:
        p.append(f"{sin_grupo} están en select sin agregar y no están en group")
    faltan, sobran = sorted(set(salida) - set(declaradas)), sorted(set(declaradas) - set(salida))
    if faltan or sobran:
        p.append(f"«columnas» declara las de salida de la consulta (las del group y los alias): faltan {faltan}, "
                 f"sobran {sobran}")
    if p:
        return None, p
    control, i = ["count(*) AS tot_filas"], 0
    for it in items:
        it["control"] = None
        if it["fn"] == "count" and it["todo"]:
            it["control"] = "tot_filas"
        elif it["fn"] in ("count", "sum", "min", "max") and not it.get("distinto"):
            i += 1
            it["control"] = f"tot_{i}"
            control.append(f"{it['expr']} AS tot_{i}")
    expr_grupo = ", ".join(it["expr"] for it in grupo)
    consulta = {
        "items": items, "salida": salida, "llave": [it["alias"] for it in grupo], "k_minimo": k,
        "select": ", ".join(it["expr"] if it["expr"] == it["alias"] else f"{it['expr']} AS {it['alias']}" for it in items),
        "group": expr_grupo, "order": expr_grupo, "select_control": ", ".join(control),
        "expuestas": sorted({it["arg"] for it in grupo} | {it["arg"] for it in items if it["fn"] in ("min", "max")}),
        "referidas": sorted({it["arg"] for it in items if it.get("arg")}),
    }
    return consulta, []


def soql_legible(q, where):
    partes = [f"SELECT {q['select']}"] + ([f"WHERE {where}"] if where else [])
    partes += [f"GROUP BY {q['group']}", f"ORDER BY {q['order']}"] if q["group"] else []
    return " ".join(partes)


def socrata_agregado(fuente, q, meta):
    """La consulta agregada en el servidor, paginada por el group, con su control sin agrupar antes y después."""
    consultas = [url_metadatos(fuente)]
    campos = campos_de(meta)
    inventadas = [c for c in q["referidas"] if c not in campos]
    if inventadas:
        return {"motivo": f"columnas que no existen en la fuente: {inventadas}", "consultas": consultas}
    p = [f"{it['fn']}({it['arg']}): {it['arg']} es {campos.get(it['arg'])} en la fuente; sum y avg piden un número"
         for it in q["items"] if it["fn"] in ("sum", "avg") and campos.get(it["arg"]) not in NUMERICOS]
    p += [f"{it['expr']}: {it['arg']} es {campos.get(it['arg'])} en la fuente; date_trunc pide una fecha"
          for it in q["items"] if it.get("trunc") and campos.get(it["arg"]) not in FECHAS]
    if p:
        return {"motivo": "; ".join(p), "consultas": consultas}
    where = fuente.get("filtro")

    def controlar():
        url = url_api(fuente, "json", {"select": q["select_control"], "where": where})
        consultas.append(url)
        r = json.loads(pedir(url))
        return r[0] if r else {}

    for _ in range(2):
        antes = controlar()
        filas, off, paginas = [], 0, []
        while True:
            url = url_api(fuente, "csv", {"select": q["select"], "where": where, "group": q["group"], "order": q["order"],
                                          "limit": str(PAGINA), "offset": str(off)})
            consultas.append(url)
            paginas.append(url)
            pagina = leer_csv_pagina(pedir(url), q["salida"], f"la página con $offset={off}")
            filas += pagina
            if len(pagina) < PAGINA:
                break
            off += PAGINA
        despues = controlar()
        if antes == despues:
            try:
                total = int(despues.get("tot_filas"))
            except (TypeError, ValueError):
                return {"motivo": f"el control sin agrupar no trae count(*): {despues}", "consultas": consultas}
            consulta = {"select": q["select"], "where": where, "group": q["group"], "order": q["order"],
                        "k_minimo": q["k_minimo"], "limit_por_pagina": PAGINA, "paginas": len(paginas)}
            origen = url_api(fuente, "csv", {"select": q["select"], "where": where, "group": q["group"],
                                             "order": q["order"], "limit": str(max(len(filas), 1))})
            return {"filas": filas, "conteo_fuente": total, "control": despues, "origen": origen,
                    "consultas": consultas, "consulta": consulta, "paginas": paginas, "version_fuente": version_fuente(meta),
                    "consulta_soql": soql_legible(q, where),
                    "conteo_de": "count(*) del servidor sin agrupar, con el mismo filtro, igual antes y después"}
    return {"motivo": "la fuente cambió mientras se descargaba (dos veces); vuelva a correr", "consultas": consultas}


def decimal_o_none(v):
    try:
        return Decimal(str(v)) if v not in (None, "") else None
    except InvalidOperation:
        return None


def pruebas_agregado(q, columnas, filas, control):
    """Lo que el servidor calcula sin agrupar contra lo que suman los grupos: si un grupo se pierde o se repite al
    paginar, la cuenta no cierra."""
    pos = {c: columnas.index(c) for c in columnas}
    estrella = next(it for it in q["items"] if it["fn"] == "count" and it["todo"])
    try:
        tamanos = [int(f[pos[estrella["alias"]]]) for f in filas]
    except ValueError:
        tamanos = None
    total = int(control.get("tot_filas") or 0)
    suma = sum(tamanos) if tamanos is not None else None
    pruebas = [{"prueba": "conteo contra la fuente", "ok": suma == total,
                "detalle": f"{len(filas)} grupos; la suma de «{estrella['alias']}» es {suma} y el count(*) del servidor "
                           f"sin agrupar es {total}"}]
    detalles, ok = [], True
    for it in q["items"]:
        if it["control"] in (None, "tot_filas"):
            if it["fn"] in ("avg",) or it.get("distinto"):
                detalles.append(f"{it['alias']}: {it['fn']}{' distinct' if it.get('distinto') else ''} no es aditivo")
            continue
        vals = [f[pos[it["alias"]]] for f in filas]
        ref = control.get(it["control"])
        if it["fn"] in ("count", "sum"):
            a = sum((decimal_o_none(v) or Decimal(0)) for v in vals)
            b = decimal_o_none(ref) or Decimal(0)
            bien = a == b if it["fn"] == "count" else abs(a - b) <= abs(b) * Decimal("1e-9") + Decimal("1e-6")
            detalles.append(f"{it['alias']}: grupos {a} · servidor {b}")
        else:
            llenos = [v for v in vals if v != ""]
            numeros = [decimal_o_none(v) for v in llenos]
            if llenos and all(x is not None for x in numeros) and decimal_o_none(ref) is not None:
                extremo = min(numeros) if it["fn"] == "min" else max(numeros)
                bien = extremo == decimal_o_none(ref)
            else:    # texto o fechas: el orden del servidor manda, así que el del total debe ser uno de los grupos
                bien = (ref in llenos) if ref not in (None, "") else not llenos
            detalles.append(f"{it['alias']}: {'coincide' if bien else 'no coincide'} con el {it['fn']} del servidor")
        ok = ok and bien
    pruebas.append({"prueba": "conservación de los agregados", "ok": ok,
                    "detalle": "; ".join(detalles) or "solo count(*), conciliado arriba"})
    if q.get("k_minimo"):
        chicos = sum(1 for n in (tamanos or []) if n < q["k_minimo"])
        pruebas.append({"prueba": f"k-anonimato (k ≥ {q['k_minimo']})", "ok": tamanos is not None and chicos == 0,
                        "detalle": f"{chicos} grupos con menos de {q['k_minimo']} filas"})
    return pruebas


# ---------------- contrato y pruebas ----------------
def revisar_llave(llave, columnas):
    ll = [llave] if isinstance(llave, str) else llave
    if not isinstance(ll, list) or not ll or not all(isinstance(k, str) and k for k in ll):
        return [], ["«llave» es una columna o una lista no vacía de columnas"]
    p = []
    rep = sorted({k for k in ll if ll.count(k) > 1})
    if rep:
        p.append(f"la llave repite columnas: {rep}")
    fuera = [k for k in ll if k not in columnas]
    if fuera:
        p.append(f"la llave {fuera} no está entre las columnas declaradas")
    return ll, p


def tabla_valida(tabla):
    return isinstance(tabla, str) and bool(TABLA.fullmatch(tabla))


def revisar_contrato(contrato):
    """Problemas del contrato antes de leer nada. Devuelve (problemas, llaves, consulta agregada o None)."""
    faltan = [k for k in ("fuente", "tabla", "columnas") if k not in contrato]
    if faltan:
        return [f"al contrato le falta {faltan}"], [], None
    fuente, cols, p = contrato["fuente"], contrato["columnas"], []
    if not tabla_valida(contrato["tabla"]):
        p.append("«tabla» es un nombre simple (letras, números, «_» o «-», hasta 64): con «/» o «..» la ingesta "
                 "escribiría o retiraría archivos fuera de --salida")
    if not isinstance(cols, dict) or not cols:
        return p + ["«columnas» es {columna: tipo}, con al menos una"], [], None
    malos = {c: t for c, t in cols.items() if t not in TIPOS}
    if malos:
        p.append(f"tipos desconocidos (se admiten {', '.join(TIPOS)}): {malos}")
    for k in ("personales_justificadas", "base_legal_sensibles"):
        if not isinstance(contrato.get(k) or {}, dict):
            p.append(f"«{k}» es {{columna: texto}}")
    tipo = fuente.get("tipo") if isinstance(fuente, dict) else None
    if tipo not in ("socrata", "local"):
        return p + ["fuente.tipo es «socrata» o «local»"], [], None
    for k in (("dominio", "conjunto", "titulo") if tipo == "socrata" else ("ruta", "titulo")):
        if not fuente.get(k):
            p.append(f"a la fuente le falta «{k}»")
    conteo = fuente.get("conteo")
    if conteo is not None and (not isinstance(conteo, int) or isinstance(conteo, bool) or conteo < 0):
        p.append("fuente.conteo es un entero: los registros que declara quien entrega el archivo")
    if contrato.get("agregado") is None:
        llaves, pl = revisar_llave(contrato.get("llave"), cols)
        return p + pl, llaves, None
    if tipo != "socrata":
        return p + ["el modo de agregados es para Socrata: la consulta la calcula el servidor"], [], None
    consulta, pa = revisar_agregado(contrato["agregado"], list(cols))
    if consulta is None:
        return p + pa, [], None
    llave = contrato.get("llave")
    if llave not in (None, []):
        ll = [llave] if isinstance(llave, str) else llave
        if not isinstance(ll, list) or sorted(ll) != sorted(consulta["llave"]):
            p.append(f"en un agregado la llave son las columnas del group ({consulta['llave']}); el contrato dice {llave}")
    return p, consulta["llave"], consulta


def convertir(tipo, v):
    if tipo == "texto":
        return v
    if tipo == "entero":
        return int(v)
    if tipo == "decimal":
        return float(v)
    if tipo == "fecha":
        return date.fromisoformat(v[:10]) if "-" in v[:10] else datetime.strptime(v[:10], "%d/%m/%Y").date()
    raise ValueError(f"tipo desconocido: {tipo}")


def comparable(tipo, v):
    return v if tipo == "fecha" else float(v)


def limite(tipo, x):
    return date.fromisoformat(x) if tipo == "fecha" and x is not None else x


def probar(contrato, columnas, llaves, filas, leido, consulta=None, descripciones=None):
    tipos = contrato["columnas"]
    descripciones = descripciones or {}
    pruebas, avisos, nulos = [], [], {}
    if consulta is not None:
        pruebas += pruebas_agregado(consulta, columnas, filas, leido["control"])
    else:
        conteo, aparte = leido["conteo_fuente"], leido.get("conteo_independiente")
        ok = len(filas) == conteo and (aparte is None or len(filas) == aparte)
        detalle = f"filas leídas {len(filas)} · conteo de la fuente {conteo} ({leido.get('conteo_de')})"
        if aparte is not None and aparte != conteo:
            detalle += f" · contado aparte {aparte}"
        if not ok and aparte is not None:
            detalle += ": dos cuentas independientes no coinciden (¿una comilla suelta dentro de un campo sin comillas?)"
        pruebas.append({"prueba": "conteo contra la fuente", "ok": ok, "detalle": detalle})
    if llaves:
        iks = [columnas.index(k) for k in llaves]
        nombre = " + ".join(llaves)
        claves = [tuple(f[i].strip() for i in iks) for f in filas]
        repetidas = len(claves) - len(set(claves))
        incompletas = sum(1 for k in claves if not all(k))
        pruebas.append({"prueba": "llave única", "ok": repetidas == 0, "detalle": f"{nombre}: {repetidas} repetidas"})
        por_parte = ""
        if len(llaves) > 1 and incompletas:
            por_parte = " (" + ", ".join(f"{k} {sum(1 for c in claves if not c[j])}" for j, k in enumerate(llaves)) + ")"
        pruebas.append({"prueba": "llave sin nulos", "ok": incompletas == 0,
                        "detalle": f"{nombre}: {incompletas} vacías{por_parte}"})
    else:
        pruebas.append({"prueba": "una sola fila (agregado sin group)", "ok": len(filas) == 1, "detalle": f"{len(filas)} filas"})
    fallas_tipo, fuera_rango, fuera_dominio, conteo_avisos = {}, {}, {}, {}
    for j, col in enumerate(columnas):
        tipo = tipos[col]
        d = descripciones.get(col)
        privada = clasificar_columna(col, d) is not None or es_sensible(col, d)   # sus ejemplos salen enmascarados
        dom = set(contrato.get("dominios", {}).get(col, []))
        rango = contrato.get("rangos", {}).get(col)
        aviso = contrato.get("avisos", {}).get(col)
        for f in filas:
            v = f[j].strip()
            if not v:
                nulos[col] = nulos.get(col, 0) + 1
                continue
            try:
                x = convertir(tipo, v)
            except (ValueError, TypeError):
                e = fallas_tipo.setdefault(col, {"cuantos": 0, "ejemplos": []})
                e["cuantos"] += 1
                if len(e["ejemplos"]) < 3:
                    e["ejemplos"].append(enmascarar(v) if privada else v[:40])
                continue
            if dom and v not in dom:
                fuera_dominio.setdefault(col, set()).add(enmascarar(v) if privada else v[:40])
            for lim, destino in ((rango, fuera_rango), (aviso, conteo_avisos)):
                if lim:
                    lo, hi = limite(tipo, lim[0]), limite(tipo, lim[1])
                    c = comparable(tipo, x)
                    if (lo is not None and c < lo) or (hi is not None and c > hi):
                        destino[col] = destino.get(col, 0) + 1
    pruebas.append({"prueba": "tipos declarados (FAILFAST)", "ok": not fallas_tipo,
                    "detalle": "todos los valores tienen su tipo" if not fallas_tipo else json.dumps(fallas_tipo, ensure_ascii=False)})
    pruebas.append({"prueba": "rangos", "ok": not fuera_rango,
                    "detalle": "dentro de los rangos declarados" if not fuera_rango else json.dumps(fuera_rango, ensure_ascii=False)})
    pruebas.append({"prueba": "dominios", "ok": not fuera_dominio,
                    "detalle": "dentro de los dominios declarados" if not fuera_dominio else
                    json.dumps({k: sorted(v)[:5] for k, v in fuera_dominio.items()}, ensure_ascii=False)})
    for col, n in conteo_avisos.items():
        avisos.append(f"{col}: {n} valores fuera de {contrato['avisos'][col]} (se reportan, no se corrigen)")
    return pruebas, avisos, nulos


def retirar(salida, tabla, motivo, escribir=True):
    """Una carga rechazada no deja datos donde los leen las etapas siguientes: si había un <tabla>.csv de una carga
    anterior, se retira y se dice; y queda la procedencia de esta carga en «rechazada» (nunca la aprobada de antes).
    Solo con un nombre de tabla simple: con «../» retiraría un archivo fuera de --salida."""
    if not tabla_valida(tabla):
        return False
    salida = Path(salida)
    destino = salida / f"{tabla}.csv"
    retirado = destino.exists()
    if retirado:
        destino.unlink()
        print(f"  · se retira {destino.name} de una carga anterior: ya no corresponde a una carga aprobada")
    if escribir:
        salida.mkdir(parents=True, exist_ok=True)
        (salida / f"procedencia_{tabla}.json").write_text(json.dumps(
            {"tabla": tabla, "estado": "rechazada", "motivo": motivo, "archivo": None, "retirado": retirado,
             "consultado": datetime.now().astimezone().isoformat(timespec="seconds")}, ensure_ascii=False, indent=2),
            encoding="utf-8")
    return retirado


def miles(n):
    return f"{n:,}".replace(",", ".")


def rechazar(motivo, salida=None, tabla=None, extra=None, lineas=()):
    for linea in lineas:
        print(f"✗ minimización: {linea}")
    print(f"Ingesta rechazada: {motivo}")
    if salida is not None:
        retirar(salida, tabla, motivo)
    print("RESUMEN " + json.dumps({"estado": "rechazada", "motivo": motivo, **(extra or {})}, ensure_ascii=False))
    return 1


def csv_de(columnas, filas):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(columnas)
    w.writerows(filas or [])
    return buf.getvalue().encode("utf-8")


def ingerir(ruta_contrato, salida, repetir=False):
    try:
        contrato = json.loads(Path(ruta_contrato).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return rechazar(f"el contrato no se puede leer: {type(e).__name__}: {str(e)[:160]}")
    if not isinstance(contrato, dict):
        return rechazar("el contrato es un objeto JSON {fuente, tabla, llave, columnas, ...}")
    problemas, llaves, consulta = revisar_contrato(contrato)
    tabla = contrato.get("tabla")
    if problemas:
        return rechazar("el contrato no se puede ejecutar: " + "; ".join(problemas), salida, tabla)
    fuente = contrato["fuente"]
    columnas = list(contrato["columnas"])
    justificadas = contrato.get("personales_justificadas") or {}
    # D7: en un agregado se miran las columnas cuyos valores salen (las del group y las de min o max); un dato sensible,
    # en cualquier parte de la consulta. Primero por el nombre, sin pedir nada a la fuente.
    revisadas = consulta["expuestas"] if consulta else columnas
    referidas = consulta["referidas"] if consulta else []
    rechazo = minimizacion(contrato, revisadas, {}, referidas)
    meta, descripciones = None, {}
    if not rechazo and fuente["tipo"] == "socrata":
        # luego por la descripción de cada columna en los metadatos: el nombre puede esconder lo que es
        try:
            meta = json.loads(pedir(url_metadatos(fuente)))
        except (FuenteError, json.JSONDecodeError, ValueError) as e:
            return rechazar(f"la fuente no respondió como se esperaba: {type(e).__name__}: {str(e)[:240]}", salida, tabla)
        if not isinstance(meta, dict):
            return rechazar("los metadatos de la fuente no son un objeto JSON", salida, tabla)
        descripciones = {c.get("fieldName"): c.get("description") or "" for c in meta.get("columns", []) if isinstance(c, dict)}
        rechazo = minimizacion(contrato, revisadas, descripciones, referidas)
    if rechazo:
        return rechazar(rechazo["motivo"], salida, tabla, {"columnas": rechazo["columnas"]}, rechazo["lineas"])
    if consulta is not None:
        def leer():
            return socrata_agregado(fuente, consulta, meta)
    elif fuente["tipo"] == "socrata":
        def leer():
            return socrata(fuente, columnas, llaves, meta)
    else:
        def leer():
            return local(fuente, columnas)

    def leer_seguro():
        try:
            return leer()
        except (FuenteError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as e:
            return {"motivo": f"la fuente no respondió como se esperaba: {type(e).__name__}: {str(e)[:240]}"}

    leido = leer_seguro()
    if leido.get("motivo"):
        return rechazar(leido["motivo"], salida, tabla)
    filas = leido["filas"]
    if consulta is not None:     # la API devuelve el orden del select; se escribe en el orden de «columnas»
        idx = [consulta["salida"].index(c) for c in columnas]
        filas = [[f[i] for i in idx] for f in filas]
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    contenido = csv_de(columnas, filas)
    if fuente["tipo"] == "local":
        problema = lector_de_reglas(contenido, salida)
        if problema:
            return rechazar(problema, salida, tabla)
    huella = hashlib.sha256(contenido).hexdigest()
    destino = salida / f"{tabla}.csv"
    anterior = hashlib.sha256(destino.read_bytes()).hexdigest() if destino.exists() else None
    repetible = None
    if repetir:
        otra = leer_seguro()
        filas2 = otra.get("filas")
        if consulta is not None and filas2 is not None:
            filas2 = [[f[i] for i in idx] for f in filas2]
        repetible = filas2 is not None and hashlib.sha256(csv_de(columnas, filas2)).hexdigest() == huella
    pruebas, avisos, nulos = probar(contrato, columnas, llaves, filas, leido, consulta, descripciones)
    if repetible is not None:
        pruebas.append({"prueba": "correr dos veces da lo mismo", "ok": repetible,
                        "detalle": "la segunda lectura dio el mismo archivo, byte a byte" if repetible
                        else "la segunda lectura dio otro archivo"})
    aprobada = all(p["ok"] for p in pruebas)
    if aprobada and anterior != huella:
        fd, tmp = tempfile.mkstemp(dir=salida, suffix=".tmp")
        with os.fdopen(fd, "wb") as fh:
            fh.write(contenido)
        os.replace(tmp, destino)     # escritura atómica: reemplaza, nunca agrega (R12)
    ahora = datetime.now().astimezone()      # con zona horaria: la hora sola no dice cuándo
    unidad = fuente.get("unidad", "filas")
    conteo_fuente = leido["conteo_fuente"]
    filtro = fuente.get("filtro_legible") or fuente.get("filtro") or "sin filtro"
    if consulta is not None:
        cita = (f"{fuente['titulo']}, {fuente['dominio'].replace('www.', '')} ({fuente['conjunto']}), {filtro}, agregado "
                f"en la fuente ({leido['consulta_soql']}), consultado el {ahora:%d-%m-%Y}. {miles(len(filas))} grupos que "
                f"resumen {miles(conteo_fuente)} {unidad}.")
    elif fuente["tipo"] == "socrata":
        cita = (f"{fuente['titulo']}, {fuente['dominio'].replace('www.', '')} ({fuente['conjunto']}), {filtro}, "
                f"consultado el {ahora:%d-%m-%Y}. {miles(len(filas))} {unidad}.")
    else:
        cita = f"{fuente['titulo']}, archivo {Path(fuente['ruta']).name}, leído el {ahora:%d-%m-%Y}. {miles(len(filas))} {unidad}."
    proc = {
        "tabla": tabla, "archivo": portable(destino), "fuente": fuente, "modo": "agregado" if consulta else "filas",
        "origen": leido.get("origen"), "llave": llaves if len(llaves) != 1 else llaves[0],
        "consulta": leido.get("consulta"), "paginas": leido.get("paginas"), "consultas": leido.get("consultas"),
        "version_fuente": leido.get("version_fuente"), "columnas": contrato["columnas"],
        "consultado": ahora.isoformat(timespec="seconds"),
        "consultado_legible": f"{ahora:%d-%m-%Y %H:%M} (UTC{ahora:%z})", "filas": len(filas), "conteo_fuente": conteo_fuente,
        "conteo_de": leido.get("conteo_de"), "conteo_independiente": leido.get("conteo_independiente"),
        "sha256": huella, "sha256_anterior": anterior, "sin_cambios": anterior == huella,
        "nulos": nulos, "avisos": avisos, "nota": leido.get("nota"), "pruebas": pruebas, "cita": cita,
        "licencia": fuente.get("licencia"), "atribucion": fuente.get("atribucion"),
        "columnas_personales_justificadas": justificadas, "base_legal_sensibles": contrato.get("base_legal_sensibles") or {},
    }
    if consulta is not None:
        proc.update(consulta_soql=leido["consulta_soql"], control_sin_agrupar=leido["control"])
    proc["estado"] = "aprobada" if aprobada else "rechazada"
    if not aprobada:
        proc["archivo"] = None
        proc["retirado"] = retirar(salida, tabla, "la carga no pasó sus pruebas", escribir=False)
    # una procedencia por tabla: con varias tablas, ninguna reemplaza a otra (ya no se escribe procedencia.json)
    (salida / f"procedencia_{tabla}.json").write_text(json.dumps(proc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ingesta {proc['estado']}: {miles(len(filas))} {'grupos' if consulta else unidad}"
          + (f" → {destino}" if aprobada else " (no se escribe el CSV: no pasó sus pruebas)"))
    for p in pruebas:
        print(f"  {'✓' if p['ok'] else '✗'} {p['prueba']}: {p['detalle']}")
    for a in avisos:
        print(f"  · aviso: {a}")
    if leido.get("nota"):
        print(f"  · nota: {leido['nota']}")
    if consulta is not None:
        print(f"  · consulta: {leido['consulta_soql']}")
    print(f"  · nulos: {nulos}")
    print(f"  · {'sin cambios frente a la carga anterior' if proc['sin_cambios'] else 'archivo escrito' if aprobada else 'sin escribir'}"
          f" · sha256 {huella}")
    print(f"  · cita: {cita}")
    print("RESUMEN " + json.dumps({"estado": proc["estado"], "filas": len(filas), "conteo_fuente": conteo_fuente,
                                   "fallas": [p["prueba"] for p in pruebas if not p["ok"]]}, ensure_ascii=False))
    return 0 if proc["estado"] == "aprobada" else 1


# ---------------- autoprueba (sin red ni datos reales) ----------------
class SocrataFalso:
    """Un Socrata de mentira sobre filas ficticias en memoria: metadatos, count(*) y consultas de filas o agregadas,
    con $order, $limit y $offset. Se puede romper a propósito: perder un grupo al paginar, cambiar la fuente en cada
    conteo o devolver una página con un campo de menos. Tiene su propio evaluador: no usa el de la ingesta."""

    def __init__(self, campos, filas, perder=None, cambiar=False, pagina_rota=False, descripciones=None):
        self.campos, self.filas = campos, [dict(f) for f in filas]
        self.perder, self.cambiar, self.pagina_rota = perder, cambiar, pagina_rota
        self.descripciones = descripciones or {}
        self.pedidas = []

    @staticmethod
    def _valor(f, expr):
        m = re.fullmatch(r"date_trunc_(ymd|ym|y)\((\w+)\)", expr)
        if not m:
            return f.get(expr, "")
        v = f.get(m.group(2), "")
        corte = {"y": 4, "ym": 7, "ymd": 10}[m.group(1)]
        return (v[:corte] + "-01-01"[:10 - corte] + "T00:00:00.000") if v else ""

    def _agregar(self, filas, items, grupo):
        grupos = {}
        for f in filas:
            grupos.setdefault(tuple(self._valor(f, g) for g in grupo), []).append(f)
        if not grupo and not grupos:
            grupos[()] = []
        salida = []
        for clave, fs in sorted(grupos.items()):
            fila = []
            for expr, _ in items:
                m = re.fullmatch(r"(count|sum|avg|min|max)\((\*|distinct \w+|\w+)\)", expr)
                if not m:
                    fila.append(clave[grupo.index(expr)])
                    continue
                fn, arg = m.groups()
                vals = [f.get(arg.replace("distinct ", ""), "") for f in fs] if arg != "*" else ["x"] * len(fs)
                llenos = [v for v in vals if v != ""]
                if fn == "count":
                    fila.append(str(len(set(llenos)) if arg.startswith("distinct ") else len(llenos)))
                elif fn in ("sum", "avg"):
                    s = sum(Decimal(v) for v in llenos)
                    fila.append("" if not llenos else str(s if fn == "sum" else s / len(llenos)))
                else:
                    num = all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in llenos)
                    clave_orden = (lambda v: Decimal(v)) if num else (lambda v: v)
                    fila.append("" if not llenos else (min if fn == "min" else max)(llenos, key=clave_orden))
            salida.append(fila)
        return salida

    def __call__(self, url, intentos=3):
        self.pedidas.append(url)
        u = urllib.parse.urlsplit(url)
        if u.path.startswith("/api/views/"):
            return json.dumps({"columns": [{"fieldName": c, "dataTypeName": t, "description": self.descripciones.get(c, "")}
                                           for c, t in self.campos.items()],
                               "rowsUpdatedAt": 1762387200})
        p = {k[1:]: v for k, v in urllib.parse.parse_qsl(u.query)}
        items = []
        for pieza in (x.strip() for x in p["select"].split(",")):
            m = re.fullmatch(r"(.+?) AS (\w+)", pieza)
            items.append((m.group(1), m.group(2)) if m else (pieza, pieza))
        grupo = [g.strip() for g in p.get("group", "").split(",") if g.strip()]
        agregada = bool(grupo) or any("(" in e for e, _ in items)
        if u.path.endswith(".json"):
            fila = self._agregar(self.filas, items, [])[0]
            if self.cambiar:
                self.filas.append(dict(self.filas[0]))
            return json.dumps([{a: v for (_, a), v in zip(items, fila) if v != ""}])
        if agregada:
            filas = self._agregar(self.filas, items, grupo)
            if self.perder is not None:
                filas = [f for f in filas if self.perder not in f]
        else:
            orden = [o.strip() for o in p.get("order", "").split(",") if o.strip()]
            filas = sorted(([f.get(e, "") for e, _ in items] for f in self.filas),
                           key=lambda r: tuple(r[[e for e, _ in items].index(o)] for o in orden))
        off, lim = int(p.get("offset", 0)), int(p.get("limit", 1000))
        filas = filas[off:off + lim]
        buf = io.StringIO()
        w = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([a for _, a in items])
        for f in filas:
            w.writerow(f[:-1] if self.pagina_rota else f)
        return buf.getvalue()


def socrata_falso(filas_fuente, meta, cab):
    """Un Socrata de prueba, sin red: pagina con $offset, ordena con $order y, sin $limit, devuelve 1.000 filas, como
    el de verdad. Sin $order, devuelve su orden «natural», que no es el de la llave."""
    def pedir_falso(url, intentos=3):
        partes = urllib.parse.urlsplit(url)
        qs = dict(urllib.parse.parse_qsl(partes.query))
        if "/api/views/" in partes.path:
            return json.dumps(meta)
        if partes.path.endswith(".json"):
            return json.dumps([{"n": str(len(filas_fuente))}])
        filas = sorted(filas_fuente, key=lambda f: f[0]) if "$order" in qs else list(filas_fuente)
        off, lim = int(qs.get("$offset", 0)), int(qs.get("$limit", 1000))
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_ALL)
        w.writerow(cab)
        w.writerows(filas[off:off + lim])
        return buf.getvalue()
    return pedir_falso


def comprobar_procedencia(mod):
    """Prueba sin red de la procedencia que deja `mod` (este módulo u otra versión de ingesta.py). Devuelve las fallas."""
    import random
    cab = ["llave", "valor"]
    filas_fuente = [[f"K{i:05d}", str(10 * i)] for i in range(2500)]
    random.Random(7).shuffle(filas_fuente)
    meta = {"columns": [{"fieldName": "llave", "description": "Identificador del registro"},
                        {"fieldName": "valor", "description": "Valor del registro"}],
            "rowsUpdatedAt": 1793866132, "viewLastModified": 1792907125}
    falso = socrata_falso(filas_fuente, meta, cab)
    viejo = (mod.pedir, mod.PAGINA)
    mod.pedir, mod.PAGINA = falso, 1000          # tres páginas de 1.000
    tmp = Path(tempfile.mkdtemp(prefix="ingesta-autoprueba-"))
    fallas = []
    try:
        contrato = {"fuente": {"tipo": "socrata", "dominio": "datos.ejemplo.invalid", "conjunto": "abcd-1234", "titulo": "Fuente de prueba",
                               "filtro": "1=1", "licencia": "—", "atribucion": "—", "unidad": "filas"},
                    "tabla": "t", "llave": "llave", "columnas": {"llave": "texto", "valor": "entero"}}
        (tmp / "t.json").write_text(json.dumps(contrato), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.ingerir(tmp / "t.json", tmp / "datos")
        p = tmp / "datos" / "procedencia_t.json"
        proc = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        if rc != 0 or proc.get("estado") != "aprobada":
            fallas.append(f"la carga de prueba no se aprobó (código {rc})")

        def huella(urls):
            filas = []
            for u in urls:
                filas += list(csv.reader(io.StringIO(falso(u))))[1:]
            buf = io.StringIO()
            w = csv.writer(buf, lineterminator="\n")
            w.writerow(cab)
            w.writerows(filas)
            return hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest(), len(filas)

        if proc.get("origen"):
            h, n = huella([proc["origen"]])
            if h != proc.get("sha256"):
                fallas.append(f"bajar «origen» no reproduce la carga: {n} filas y otra huella (la carga: {proc.get('filas')} filas)")
        else:
            fallas.append("la procedencia no trae «origen»")
        if not proc.get("paginas") or huella(proc["paginas"])[0] != proc.get("sha256"):
            fallas.append("la procedencia no trae la lista de páginas que reproduce la carga")
        if (proc.get("consulta") or {}).get("order") != "llave":
            fallas.append("la procedencia no guarda la consulta completa (select, where, order y tamaño de página)")
        try:
            con_zona = datetime.fromisoformat(proc.get("consultado") or "").tzinfo is not None
        except ValueError:
            con_zona = False
        if not con_zona:
            fallas.append(f"«consultado» sin zona horaria: {proc.get('consultado')}")
        if (proc.get("version_fuente") or {}).get("rowsUpdatedAt") != meta["rowsUpdatedAt"]:
            fallas.append("la procedencia no guarda la versión de la fuente (rowsUpdatedAt, viewLastModified)")
    finally:
        mod.pedir, mod.PAGINA = viejo
        shutil.rmtree(tmp, ignore_errors=True)
    return fallas


def comprobar_varias_tablas(mod):
    """Dos tablas en la misma --salida (el ejemplo local del README): ventas con la llave repetida, clientes correcta.
    La rechazada no deja su CSV (ni el de una carga anterior), cada tabla tiene su procedencia, la etapa no queda
    aprobada y verificar.py nota un crudo alterado después de ingerido. Devuelve las fallas."""
    import rutas
    import verificar
    tmp = Path(tempfile.mkdtemp(prefix="ingesta-tablas-"))
    salida = tmp / "corrida" / "datos"
    fallas = []
    try:
        def cargar(tabla, texto, cols):
            (tmp / f"{tabla}.csv").write_text(texto, encoding="utf-8")
            (tmp / f"{tabla}.json").write_text(json.dumps({
                "fuente": {"tipo": "local", "ruta": str(tmp / f"{tabla}.csv"), "titulo": "Datos de prueba", "licencia": "—",
                           "atribucion": "—", "unidad": "filas"}, "tabla": tabla, "llave": "id",
                "columnas": {c: "texto" for c in cols}}), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                return mod.ingerir(tmp / f"{tabla}.json", salida)
        cargar("ventas", "id,valor\n1,10\n2,20\n", ["id", "valor"])           # una carga anterior, aprobada
        rc_v = cargar("ventas", "id,valor\n1,10\n1,20\n2,30\n", ["id", "valor"])  # la de hoy: la llave se repite
        rc_c = cargar("clientes", "id,region\nC1,Norte\nC2,Sur\n", ["id", "region"])
        if rc_v == 0 or rc_c != 0:
            fallas.append(f"códigos inesperados: ventas {rc_v} (se esperaba 1), clientes {rc_c} (se esperaba 0)")
        if (salida / "ventas.csv").exists():
            fallas.append("la carga rechazada de ventas dejó ventas.csv en --salida, donde lo leen las etapas siguientes")
        if (salida / "procedencia.json").exists():
            fallas.append("se escribe el procedencia.json genérico: con dos tablas, la última reemplaza a la otra")
        spec = {"datos": {"ventas": str(salida / "ventas.csv"), "clientes": str(salida / "clientes.csv")}}
        procs = rutas.procedencias(tmp / "corrida", spec)
        if (procs.get("ventas") or {}).get("estado") != "rechazada" or (procs.get("clientes") or {}).get("estado") != "aprobada":
            fallas.append(f"no hay una procedencia por tabla: {({t: (p or {}).get('estado') for t, p in procs.items()})}")
        if rutas.estado_ingesta(procs) is not False:
            fallas.append("con una tabla rechazada, la etapa Ingesta no queda en ⚠️")
        solo_clientes = {"datos": {"clientes": str(salida / "clientes.csv")}}
        _, antes = verificar.revisar_procedencias(tmp / "corrida", solo_clientes)
        with open(salida / "clientes.csv", "a", encoding="utf-8") as fh:
            fh.write("C3,Este\n")
        _, despues = verificar.revisar_procedencias(tmp / "corrida", solo_clientes)
        if antes or not despues:
            fallas.append(f"verificar.py no nota un crudo alterado después de ingerido (antes {antes}, después {despues})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return fallas


def autoprueba(mod=None):
    """Casos ficticios, sin red ni datos reales. Con mod se prueba otro módulo de ingesta (p. ej. la versión anterior)
    con los mismos casos: así se demuestra que cada caso falla antes del arreglo y pasa después."""
    mod = mod or sys.modules[__name__]
    tmp = Path(tempfile.mkdtemp(prefix="ingesta-autoprueba-"))
    resultados = []

    def correr(nombre, contrato, espera, condicion=None, falso=None, pagina=None, repetir=False):
        d = tmp / f"caso{len(resultados):02d}"
        d.mkdir()
        (d / "contrato.json").write_text(json.dumps(contrato, ensure_ascii=False), encoding="utf-8")
        viejos = (mod.pedir, mod.PAGINA)
        if falso is not None:
            mod.pedir = falso
        if pagina:
            mod.PAGINA = pagina
        buf, codigo, error = io.StringIO(), None, None
        try:
            with contextlib.redirect_stdout(buf):
                codigo = mod.ingerir(str(d / "contrato.json"), str(d / "salida"), repetir=repetir)
        except BaseException as e:  # noqa: BLE001 (la versión anterior revienta; eso también es una falla)
            error = f"{type(e).__name__}: {str(e)[:120]}"
        finally:
            mod.pedir, mod.PAGINA = viejos
        linea = next((x for x in reversed(buf.getvalue().splitlines()) if x.startswith("RESUMEN ")), None)
        resumen = json.loads(linea[len("RESUMEN "):]) if linea else {}
        p_proc = d / "salida" / f"procedencia_{contrato.get('tabla')}.json"
        proc = json.loads(p_proc.read_text(encoding="utf-8")) if p_proc.exists() else {}
        estado = resumen.get("estado")     # espera=None: vale cualquier estado; manda la condición
        ok = (error is None and estado in ("aprobada", "rechazada") and estado == (espera or estado)
              and codigo == (0 if estado == "aprobada" else 1))
        motivo_cond = ""
        if ok and condicion is not None:
            try:
                ok = bool(condicion(resumen, proc, falso, d))
            except Exception as e:  # noqa: BLE001
                ok, motivo_cond = False, f"{type(e).__name__}: {e}"
        detalle = error or f"{resumen.get('estado')} · {str(resumen.get('motivo') or resumen.get('fallas'))[:110]}{motivo_cond}"
        resultados.append((nombre, ok, detalle))

    def con_linea(r, *_):
        return bool(re.search(r"l[ií]nea \d+", str(r.get("motivo") or "")))

    def falla(nombre):
        return lambda r, *_: nombre in (r.get("fallas") or [])

    def local_(ruta, columnas, llave, **extra):
        fuente = {"tipo": "local", "ruta": str(ruta), "titulo": "caso ficticio", "licencia": "—", "atribucion": "—",
                  "unidad": "filas", **extra.pop("fuente", {})}
        return {"fuente": fuente, "tabla": "caso", "llave": llave, "columnas": columnas,
                "personales_justificadas": {c: "caso de prueba con valores ficticios" for c in columnas}, **extra}

    def archivo(nombre, contenido):
        ruta = tmp / nombre
        ruta.write_bytes(contenido if isinstance(contenido, bytes) else contenido.encode("utf-8"))
        return ruta

    def cabecera(ruta):
        with open(ruta, newline="", encoding="utf-8-sig", errors="replace") as fh:
            return next(csv.reader(fh), None) or ["vacio"]

    # 1. FAILFAST local: cada CSV de baterias/failfast y otros casos rotos se rechazan diciendo la línea
    for ruta in sorted((AQUI.parent / "baterias" / "failfast").glob("*.csv")):
        cab = cabecera(ruta)
        correr(f"failfast {ruta.name}", local_(ruta, {c: "texto" for c in cab}, cab[0]), "rechazada", con_linea)
    rotos = {
        "coma sin comillas («2,Medellin, Antioquia,200»)": "id,ciudad,valor\n1,Bogota,100\n2,Medellin, Antioquia,200\n",
        "miles con coma sin comillas («2,1,500»)": "id,valor\n1,1000\n2,1,500\n3,2000\n",
        "línea vacía en medio": "id,valor\n1,10\n\n2,20\n",
        "solo el encabezado": "id,valor\n",
        "archivo vacío": "",
        "encabezado con columnas repetidas": "id,valor,valor\n1,10,20\n",
        "comilla sin cerrar en la última fila": 'id,valor\n1,10\n2,"20\n',
        "carácter nulo": "id,valor\n1,1\x000\n",
        "no está en UTF-8 (Windows-1252)": "id,ciudad\n1,Medellín\n".encode("cp1252"),
    }
    for nombre, contenido in rotos.items():
        ruta = archivo(f"roto{len(resultados):02d}.csv", contenido)
        cab = cabecera(ruta)
        correr(f"failfast {nombre}", local_(ruta, {c: "texto" for c in dict.fromkeys(cab)}, cab[0]), "rechazada", con_linea)
    ruta = archivo("abre.csv", 'id,nota\n1,a\n2,"sin cerrar\n3,b\n4,c\n')
    correr("comilla sin cerrar: el motivo dice la línea donde se abre (3), no solo la última",
           local_(ruta, {"id": "texto", "nota": "texto"}, "id"), "rechazada",
           lambda r, *_: "la línea 3 " in str(r.get("motivo")))
    ruta = archivo("monto.csv", "id,valor\n1,78.000\n2,1628100\n")
    correr("failfast monto con punto de miles declarado decimal", local_(ruta, {"id": "texto", "valor": "decimal"}, "id"),
           "rechazada", con_linea)
    ruta = archivo("doc.csv", "id,numero_documento\n1,1.035.233.887\n2,43\n")
    correr("punto de miles en una columna personal: el motivo no muestra el valor",
           local_(ruta, {"id": "texto", "numero_documento": "texto"}, "id"), "rechazada",
           lambda r, *_: con_linea(r) and "035" not in str(r.get("motivo")))
    ruta = archivo("decimal.csv", "id,peso_kg\n1,12.5\n2,1.250\n3,1500\n")
    correr("con 12.5 en la columna, 1.250 es un decimal y se carga (L49)", local_(ruta, {"id": "texto", "peso_kg": "decimal"}, "id"),
           "aprobada")
    ruta = archivo("suelta.csv", 'id,medida\n1,5"\n2,7\n')
    correr("comilla suelta: dos cuentas independientes no coinciden", local_(ruta, {"id": "texto", "medida": "texto"}, "id"),
           "rechazada", falla("conteo contra la fuente"))
    ruta = archivo("declarado.csv", "id,valor\n1,10\n2,20\n")
    correr("el conteo que declara el contrato (5) no coincide con el archivo (2)",
           local_(ruta, {"id": "texto", "valor": "entero"}, "id", fuente={"conteo": 5}), "rechazada", falla("conteo contra la fuente"))
    # controles positivos: los CSV bien formados se leen completos
    for ruta in sorted((AQUI.parent / "ejemplo" / "datos").glob("*.csv")):
        cab = cabecera(ruta)
        with open(ruta, newline="", encoding="utf-8-sig") as fh:
            esperado = sum(1 for _ in csv.DictReader(fh))
        correr(f"control {ruta.name}: se lee completo", local_(ruta, {c: "texto" for c in cab}, cab[0]), None,
               lambda r, p, f, d, e=esperado: r.get("filas") == e == r.get("conteo_fuente") and not r.get("motivo")
               and "conteo contra la fuente" not in r.get("fallas", []) and "tipos declarados (FAILFAST)" not in r.get("fallas", []))
    ruta = archivo("crlf.csv", '﻿id,nota\r\n1,"dos\r\nlíneas"\r\n2,b\r\n')
    correr("control CRLF, BOM y un campo con salto de línea, conservado byte a byte",
           local_(ruta, {"id": "texto", "nota": "texto"}, "id"), "aprobada",
           lambda r, p, f, d: r.get("filas") == 2 and p.get("nota") and ((d / "salida" / "caso.csv").read_bytes().decode("utf-8")
                                                                         == 'id,nota\n1,"dos\r\nlíneas"\n2,b\n'))
    # el contrato: roto o con un nombre de tabla que sale de --salida se rechaza sin traceback
    centinela = archivo("fuera.csv", "no se toca\n")
    correr("tabla «../../fuera»: se rechaza y no retira (borra) ni escribe un archivo fuera de --salida",
           {**local_(archivo("dos.csv", "id,valor\n1,10\n1,20\n"), {"id": "texto", "valor": "texto"}, "id"), "tabla": "../../fuera"},
           "rechazada", lambda r, *_: "tabla" in str(r.get("motivo")) and centinela.exists())
    correr("contrato con un tipo desconocido", local_(centinela, {"id": "numerico"}, "id"), "rechazada",
           lambda r, *_: "tipos desconocidos" in str(r.get("motivo")))
    d_roto = tmp / "roto.json"
    d_roto.write_text("{no es json", encoding="utf-8")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.ingerir(str(d_roto), str(tmp / "salida-rota"))
        ok = rc == 1 and '"estado": "rechazada"' in buf.getvalue()
    except BaseException as e:  # noqa: BLE001
        ok = False
    resultados.append(("contrato que no es JSON: RESUMEN «rechazada», no traceback", ok, buf.getvalue()[-110:]))
    # 2. llaves compuestas
    clientes = AQUI.parent / "ejemplo" / "datos" / "clientes.csv"
    tipos_cli = {"cliente_id": "texto", "nombre": "texto", "region": "texto", "fecha_actualizacion": "fecha"}
    correr("llave compuesta (cliente_id + fecha_actualizacion) única", local_(clientes, tipos_cli, ["cliente_id", "fecha_actualizacion"]),
           "aprobada", lambda r, p, *_: p.get("llave") == ["cliente_id", "fecha_actualizacion"])
    correr("la misma tabla con llave simple cliente_id: se repite", local_(clientes, tipos_cli, "cliente_id"), "rechazada",
           falla("llave única"))
    ruta = archivo("estaciones.csv", "estacion,fecha,mm\nE1,2025-01-01,3\nE1,2025-01-02,4\nE2,2025-01-01,0\n,2025-01-03,1\nE2,2025-01-01,5\n")
    tipos_est = {"estacion": "texto", "fecha": "fecha", "mm": "decimal"}
    correr("llave compuesta con una parte vacía y una combinación repetida", local_(ruta, tipos_est, ["estacion", "fecha"]),
           "rechazada", lambda r, *_: {"llave única", "llave sin nulos"} <= set(r.get("fallas", [])))
    for nombre, llave in (("repite una columna", ["estacion", "estacion"]), ("no declarada", ["estacion", "hora"]),
                          ("vacía", [])):
        correr(f"llave compuesta mal escrita: {nombre}", local_(ruta, tipos_est, llave), "rechazada",
               lambda r, *_: "llave" in str(r.get("motivo")))
    filas_est = [{"estacion": e, "fecha": f, "mm": m} for e, f, m in
                 (("E2", "2025-01-01", "0"), ("E1", "2025-01-02", "4"), ("E1", "2025-01-01", "3"))]
    soc = {"tipo": "socrata", "dominio": "datos.ficticio.invalid", "conjunto": "abcd-1234", "titulo": "fuente ficticia",
           "filtro": "1=1", "licencia": "—", "atribucion": "—", "unidad": "filas"}
    campos_est = {"estacion": "text", "fecha": "calendar_date", "mm": "number"}
    falso = SocrataFalso(campos_est, filas_est)
    correr("Socrata por filas con llave compuesta: $order por las dos columnas",
           {"fuente": soc, "tabla": "est", "llave": ["estacion", "fecha"], "columnas": tipos_est}, "aprobada",
           lambda r, p, f, d: any("%24order=estacion%2Cfecha" in u for u in f.pedidas) and p.get("version_fuente")
           and p.get("consultas"), falso)
    correr("Socrata por filas: la fuente cambia durante la descarga",
           {"fuente": soc, "tabla": "est", "llave": ["estacion", "fecha"], "columnas": tipos_est}, "rechazada",
           lambda r, *_: "cambió" in str(r.get("motivo")), SocrataFalso(campos_est, filas_est, cambiar=True))
    correr("Socrata por filas: una página con un campo de menos",
           {"fuente": soc, "tabla": "est", "llave": ["estacion", "fecha"], "columnas": tipos_est}, "rechazada",
           lambda r, *_: "campos" in str(r.get("motivo")), SocrataFalso(campos_est, filas_est, pagina_rota=True))
    f = SocrataFalso({**campos_est, "campo_7": "text"}, filas_est, descripciones={"campo_7": "Número de cédula del titular"})
    correr("Socrata: una columna personal por su descripción (campo_7: «Número de cédula») sin justificar",
           {"fuente": soc, "tabla": "est", "llave": ["estacion", "fecha"], "columnas": {**tipos_est, "campo_7": "texto"}},
           "rechazada", lambda r, p, f, d: "campo_7" in str(r.get("columnas")) and len(f.pedidas) == 1, f)
    # 3. agregados del servidor (filas ficticias: un proceso se repite por cada adjudicación)
    procesos = [{"id_del_proceso": i, "modalidad": m, "valor": v, "fecha": f, "nombre_proveedor": n} for i, m, v, f, n in (
        ("P1", "Directa", "100", "2025-01-05T00:00:00.000", "Proveedor ficticio 1"),
        ("P1", "Directa", "50", "2025-01-05T00:00:00.000", "Proveedor ficticio 2"),
        ("P2", "Directa", "70.5", "2025-02-11T00:00:00.000", "Proveedor ficticio 3"),
        ("P3", "Licitación", "1000", "2025-02-20T00:00:00.000", "Proveedor ficticio 4"),
        ("P4", "Mínima cuantía", "8", "2025-03-01T00:00:00.000", "Proveedor ficticio 5"),
        ("P4", "Mínima cuantía", "", "2025-03-01T00:00:00.000", "Proveedor ficticio 6"),
        ("P5", "Licitación", "300", "2025-01-30T00:00:00.000", "Proveedor ficticio 7"))]
    campos_p = {"id_del_proceso": "text", "modalidad": "text", "valor": "number", "fecha": "calendar_date",
                "nombre_proveedor": "text"}

    def agregado(select, group, columnas, **extra):
        ag = {"select": select, "group": group, **extra.pop("agregado", {})}
        return {"fuente": soc, "tabla": "agr", "columnas": columnas, "agregado": ag, **extra}

    tipos_ag = {"modalidad": "texto", "filas": "entero", "procesos": "entero", "valor": "decimal", "minimo": "decimal",
                "ultima": "fecha"}
    sel = ("modalidad, count(*) AS filas, count(distinct id_del_proceso) AS procesos, sum(valor) AS valor, "
           "min(valor) AS minimo, max(fecha) AS ultima")

    def bien_agregado(r, p, f, d):
        texto = (d / "salida" / "agr.csv").read_text(encoding="utf-8")
        filas_origen = list(csv.reader(io.StringIO(f(p["origen"]))))[1:]
        return (p.get("modo") == "agregado" and "GROUP BY modalidad" in p.get("consulta_soql", "")
                and len(p.get("sha256", "")) == 64 and p.get("consultado") and p.get("llave") == "modalidad"
                and any("%24offset=2" in u and "%24group=modalidad" in u for u in p.get("consultas", []))
                and (p.get("consulta") or {}).get("group") == "modalidad" and len(p.get("paginas") or []) == 2
                and len(filas_origen) == 3 and "Directa,3,2,220.5,50,2025-02-11T00:00:00.000" in texto
                and r.get("conteo_fuente") == 7)

    correr("agregado por modalidad, paginado de a 2 grupos, con procedencia", agregado(sel, "modalidad", tipos_ag),
           "aprobada", bien_agregado, SocrataFalso(campos_p, procesos), pagina=2)
    correr("agregado: correr dos veces da lo mismo", agregado(sel, "modalidad", tipos_ag), "aprobada",
           lambda r, *_: "correr dos veces da lo mismo" not in r.get("fallas", []), SocrataFalso(campos_p, procesos),
           repetir=True)
    correr("agregado por mes y modalidad: la llave es el group compuesto",
           agregado("date_trunc_ym(fecha) AS mes, modalidad, count(*) AS filas, sum(valor) AS valor", "date_trunc_ym(fecha), modalidad",
                    {"mes": "fecha", "modalidad": "texto", "filas": "entero", "valor": "decimal"}, llave=["modalidad", "mes"]),
           "aprobada", lambda r, p, *_: p.get("llave") == ["mes", "modalidad"] and r.get("filas") == 5,
           SocrataFalso(campos_p, procesos))
    correr("agregado global sin group: una sola fila",
           agregado("count(*) AS filas, sum(valor) AS valor", "", {"filas": "entero", "valor": "decimal"}), "aprobada",
           lambda r, *_: r.get("filas") == 1, SocrataFalso(campos_p, procesos))
    correr("agregado: un grupo se pierde al paginar (el CSV no se escribe)", agregado(sel, "modalidad", tipos_ag), "rechazada",
           lambda r, p, f, d: falla("conteo contra la fuente")(r) and not (d / "salida" / "agr.csv").exists(),
           SocrataFalso(campos_p, procesos, perder="Licitación"), pagina=2)
    correr("agregado: la fuente cambia durante la descarga", agregado(sel, "modalidad", tipos_ag), "rechazada",
           lambda r, *_: "cambió" in str(r.get("motivo")), SocrataFalso(campos_p, procesos, cambiar=True))
    correr("agregado: k-anonimato (k = 3) con un grupo de 2 filas",
           agregado(sel, "modalidad", tipos_ag, agregado={"k_minimo": 3}), "rechazada", falla("k-anonimato (k ≥ 3)"),
           SocrataFalso(campos_p, procesos))
    # consultas que se rechazan sin pedir nada a la fuente (o solo los metadatos)
    malas = {
        "columna sin agregar fuera del group": ("modalidad, valor, count(*) AS filas", "modalidad",
                                                {"modalidad": "texto", "valor": "decimal", "filas": "entero"}, 0),
        "función no permitida (stddev_pop)": ("modalidad, count(*) AS filas, stddev_pop(valor) AS d", "modalidad",
                                              {"modalidad": "texto", "filas": "entero", "d": "decimal"}, 0),
        "sin count(*)": ("modalidad, sum(valor) AS valor", "modalidad", {"modalidad": "texto", "valor": "decimal"}, 0),
        "agregado sin alias": ("modalidad, count(*) AS filas, sum(valor)", "modalidad",
                               {"modalidad": "texto", "filas": "entero"}, 0),
        "columnas del contrato distintas de la salida": ("modalidad, count(*) AS filas", "modalidad",
                                                         {"modalidad": "texto", "n": "entero"}, 0),
        "alias con el prefijo calidad_": ("modalidad, count(*) AS calidad_ok", "modalidad",
                                          {"modalidad": "texto", "calidad_ok": "entero"}, 0),
        "columna inventada": ("modalidad, count(*) AS filas, sum(valor_inventado) AS v", "modalidad",
                              {"modalidad": "texto", "filas": "entero", "v": "decimal"}, 1),
        "sum sobre una columna de texto": ("modalidad, count(*) AS filas, sum(id_del_proceso) AS v", "modalidad",
                                           {"modalidad": "texto", "filas": "entero", "v": "decimal"}, 1),
    }
    for nombre, (s, g, cols, pedidas) in malas.items():
        f = SocrataFalso(campos_p, procesos)
        correr(f"agregado mal escrito: {nombre}", agregado(s, g, cols), "rechazada",
               lambda r, p, f, d, n=pedidas: len(f.pedidas) == n and r.get("motivo"), f)
    f = SocrataFalso(campos_p, procesos)
    correr("agregado con order (cambia qué grupos llegan)",
           agregado("modalidad, count(*) AS filas", "modalidad", {"modalidad": "texto", "filas": "entero"},
                    agregado={"order": "filas DESC"}), "rechazada", lambda r, p, f, d: not f.pedidas, f)
    f = SocrataFalso(campos_p, procesos)
    correr("agregado con group por una columna personal sin justificar",
           agregado("nombre_proveedor, count(*) AS filas", "nombre_proveedor", {"nombre_proveedor": "texto", "filas": "entero"}),
           "rechazada", lambda r, p, f, d: not f.pedidas and "personales" in str(r.get("motivo")), f)
    f = SocrataFalso({**campos_p, "discapacidad": "text"}, procesos)
    correr("agregado que solo cuenta un dato sensible (count(distinct discapacidad)) sin base legal",
           agregado("modalidad, count(*) AS filas, count(distinct discapacidad) AS d", "modalidad",
                    {"modalidad": "texto", "filas": "entero", "d": "entero"}),
           "rechazada", lambda r, p, f, d: not f.pedidas and "base legal" in str(r.get("motivo")), f)
    f = SocrataFalso(campos_p, procesos)
    correr("agregado con la llave distinta del group",
           agregado("modalidad, count(*) AS filas", "modalidad", {"modalidad": "texto", "filas": "entero"}, llave="filas"),
           "rechazada", lambda r, p, f, d: not f.pedidas, f)
    correr("agregado sobre una fuente local", {**local_(clientes, tipos_cli, "cliente_id"),
                                                 "agregado": {"select": "region, count(*) AS n", "group": "region"}},
           "rechazada", lambda r, *_: "Socrata" in str(r.get("motivo")))
    # 4. la API: un error de la consulta (HTTP 400) no se repite; un 503 sí
    llamadas = []

    def abrir(codigo):
        def _abrir(req, timeout=None):
            llamadas.append(codigo)
            raise urllib.error.HTTPError(req.full_url, codigo, "error", {}, io.BytesIO(b'{"message": "consulta mala"}'))
        return _abrir

    for codigo, esperadas in ((400, 1), (503, 3)):
        llamadas.clear()
        viejos = (mod.urllib.request.urlopen, mod.time.sleep)
        mod.urllib.request.urlopen, mod.time.sleep = abrir(codigo), (lambda s: None)
        try:
            mod.pedir("https://datos.ficticio.invalid/resource/x.json")
            ok, det = False, "no lanzó"
        except Exception as e:  # noqa: BLE001
            ok, det = len(llamadas) == esperadas and type(e).__name__ == "FuenteError", f"{type(e).__name__} · {len(llamadas)} pedidos"
        finally:
            mod.urllib.request.urlopen, mod.time.sleep = viejos
        resultados.append((f"HTTP {codigo}: {esperadas} pedido(s) y un rechazo legible", ok, det))
    # 5. la procedencia reproduce la carga (GOB-2) y varias tablas en la misma salida (GOB-7)
    shutil.rmtree(tmp, ignore_errors=True)
    for nombre, fn in (("procedencia: la consulta guardada reproduce la carga, con su versión y su hora con zona",
                        comprobar_procedencia),
                       ("varias tablas: una procedencia por tabla, la rechazada no deja CSV y la huella del crudo se comprueba",
                        comprobar_varias_tablas)):
        try:
            fallas = fn(mod)
        except Exception as e:  # noqa: BLE001
            fallas = [f"{type(e).__name__}: {str(e)[:120]}"]
        resultados.append((nombre, not fallas, "; ".join(fallas)))
    for nombre, ok, detalle in resultados:
        print(f"{'✓' if ok else '✗'} {nombre}" + ("" if ok else f" · {detalle}"))
    malos = [n for n, ok, _ in resultados if not ok]
    print("RESUMEN " + json.dumps({"casos": len(resultados), "fallas": len(malos)}, ensure_ascii=False))
    return 1 if malos else 0


def main(argv):
    if "--autoprueba" in argv:
        return autoprueba()
    if len(argv) < 3 or "--salida" not in argv:
        raise SystemExit(__doc__)
    salida = argv[argv.index("--salida") + 1]
    return ingerir(argv[0], salida, repetir="--repetir" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
