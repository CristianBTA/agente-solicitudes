#!/usr/bin/env python3
"""Valida sin IA el whitepaper que escribe el documentador (etapa 3 · Análisis).

Uso:
  python herramientas/validar_whitepaper.py <corrida>       valida <corrida>/whitepaper.md y escribe whitepaper_verificacion.json
  python herramientas/validar_whitepaper.py --autoprueba    ejemplos ficticios buenos y malos: cada chequeo atrapa lo suyo

Desde el 6-nov-2026 el análisis lo hacen las personas del curso: la IA resume lo desarrollado para que ellas
analicen, pero no da el análisis. El whitepaper pasa si:
  W1 tiene las secciones obligatorias, en orden y con contenido: Pregunta · Datos y procedencia · Limpieza ·
     Cifra verificada y cómo se verificó · Gráfico · Gobernanza · Límites · Preguntas para el análisis de las personas;
  W2 cada cifra del texto está en los artefactos verificados de la corrida (informe.json, procedencia*.json,
     limpieza_*.json, gobernanza.json y grafico_verificacion.json, y solo si están aprobados), con tolerancia de
     redondeo. Cuentan los números de esos archivos, las cifras de los textos que escriben las herramientas
     (detalle, mensaje, cita, avisos…; no la prosa de la IA, como la razón del anticipo), el número de elementos de
     cada lista y el total de cada columna del resultado aprobado. Se permiten años, fechas, referencias legales y
     técnicas (Ley 1581 de 2012, SHA-256, CC BY-SA 4.0) e identificadores (R1, P3, D15). Las cifras van en formato
     colombiano (punto para miles, coma para decimales). Una magnitud con palabras («la mitad», «la mayoría») no se
     puede comprobar y no pasa. La sección de la cifra verificada cita al menos un total del resultado aprobado;
  W3 no trae conclusiones, recomendaciones, causas ni juicios («se concluye», «demuestra que», «se recomienda»,
     «debería», «se ahorra», «la causa es», «se debe a»…), ni títulos de conclusiones, hallazgos o análisis;
  W4 la sección de preguntas trae al menos 3, cada una con «¿» y «?», y al menos una de costo, una de calidad y
     una de impacto (rótulo al inicio de cada pregunta);
  W5 no trae instrucciones para agentes, datos personales (los patrones de gobernanza.py) ni texto oculto
     (comentarios HTML, marcado HTML, caracteres invisibles o bidireccionales).
Un whitepaper es prosa breve: más de 200 KB, líneas de más de 4.000 caracteres o una validación de más de 60 s
lo rechazan (falla cerrado; así un texto hecho para trabar las expresiones regulares no detiene el pipeline).
Sale con 1 si algo falla. La salida guarda la huella del whitepaper validado y nunca copia un dato personal
(van enmascarados) ni un texto-instrucción.
"""
import hashlib
import json
import math
import re
import signal
import sys
import time
import unicodedata
from bisect import bisect_left, bisect_right
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from gobernanza import PATRONES, enmascarar, parece_instruccion  # noqa: E402

SECCIONES = [  # (título, patrón sobre el título normalizado: minúsculas, sin tildes ni numeración)
    ("Pregunta", r"(la )?pregunta\b"),
    ("Datos y procedencia", r"(los )?datos y (su )?procedencia\b"),
    ("Limpieza", r"(la )?limpieza\b"),
    ("Cifra verificada y cómo se verificó", r"(la )?cifra verificada\b"),
    ("Gráfico", r"(el )?grafico\b"),
    ("Gobernanza", r"(la )?gobernanza\b"),
    ("Límites", r"(los )?limites\b"),
    ("Preguntas para el análisis de las personas", r"preguntas para el analisis\b"),
]
CIFRA, PREGUNTAS = SECCIONES[3][0], SECCIONES[7][0]
TIPOS = ("costo", "calidad", "impacto")
CHEQUEOS = ("W1 secciones obligatorias", "W2 cifras de los artefactos verificados",
            "W3 sin conclusiones, recomendaciones ni causas", "W4 preguntas para las personas",
            "W5 sin instrucciones, datos personales ni texto oculto")
MAX_BYTES, LINEA_MAX, TIEMPO_MAX = 200_000, 4_000, 60

# W2 · de dónde salen las cifras verificadas
ESTADO_APROBADO = {"informe.json": "aprobado", "gobernanza.json": "aprobado", "grafico_verificacion.json": "aprobado",
                   "procedencia": "aprobada", "limpieza": "aprobada"}
TEXTOS_DE_HERRAMIENTA = {"detalle", "mensaje", "cita", "avisos", "ejemplos", "prueba", "comprobacion",
                         "consultado_legible", "motivos", "problemas", "licencia"}
SALTAR = {"caso_conocido"}   # el caso con respuesta conocida son datos ficticios: sus cifras no son de la corrida
MAGNITUDES = [(r"mil\s+billones", 1e15), (r"(?:mil|miles\s+de)\s+millones", 1e9), (r"bill[oó]n(?:es)?", 1e12),
              (r"mill[oó]n(?:es)?", 1e6), (r"mil", 1e3)]
MAGNITUD = re.compile(r"\s*(" + "|".join(p for p, _ in MAGNITUDES) + r")\b", re.I)
PORCENTAJE = re.compile(r"\s*(?:%|por\s+ciento\b)", re.I)
ES_NUMERO = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")      # 17.248.249,69 · 49.662 · 17,2 · 2025
TOKEN = re.compile(r"(?<![\w.,])\d(?:[\d.,]{0,40}\d)?(?![\w])")
CIENTIFICA = re.compile(r"(?<![\w.,])(\d{1,20})(?:[.,](\d{1,20}))?[eE]([+-]?\d{1,4})(?![\w])")
CIFRA_DE_HERRAMIENTA = re.compile(r"\d+(?:[.,]\d+)*(?:[eE][+-]?\d+)?")
MES = (r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre|"
       r"ene|feb|mar|abr|may|jun|jul|ago|sept|sep|set|oct|nov|dic)")
PERMITIDOS = [  # se quitan antes de buscar cifras (se cambian por espacios: las posiciones no se mueven)
    re.compile(r"\]\([^)\s]*\)"),                                                       # destino de un enlace
    re.compile(r"https?://\S+"),
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}(?:[T ]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?\b"),   # 2026-11-06, con hora
    re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"),                                    # 06-11-2026
    re.compile(rf"\b\d{{1,2}}(?:\s+de\s+|\s*[-/]\s*|\s+){MES}\b\.?(?:(?:\s+de\s+|\s*[-/]\s*|\s+)\d{{4}}\b)?", re.I),
    re.compile(rf"\b{MES}\b\.?(?:\s+de\s+|\s*[-/]\s*|\s+)\d{{4}}\b", re.I),             # noviembre de 2026
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),                                         # 05:29
    re.compile(r"\b(?:leyes|ley|decretos?|resoluci[oó]n(?:es)?|circular(?:es)?|conpes|acuerdos?|sentencias?|art[ií]culos?|"
               r"art\.|numerales?|literal(?:es)?|par[aá]grafos?)\s+(?:[A-Z]{1,2}-)?\d+(?:[.-]\d+)*"
               r"(?:\s*(?:,|y)\s*\d+(?:[.-]\d+)*)*(?:\s+de\s+(?:19|20)\d{2})?\b", re.I),   # Ley 1581 de 2012
    re.compile(r"\bISO(?:/IEC)?\s+\d+(?::\d{4})?|\bSHA-?\d+\b|\bCC\s+BY(?:-(?:SA|NC|ND))*\s+\d+(?:\.\d+)?\b|\bUTF-?\d+\b|"
               r"\bWCAG\s+\d+(?:\.\d+)*\b|\b(?:python|pandas|numpy|plotly|bandit)\s+\d+(?:\.\d+)+\b", re.I),
    re.compile(r"(?<!\w)_+|_+(?!\w)"),                                                   # cursivas con _ (no son identificadores)
    re.compile(r"\b\w*_\w*\b"),                                                          # columnas, marcas y archivos
    re.compile(r"\b[^\W\d_]+\d\w*\b"),                                                    # R1, P3, D15, CT07, log10
    re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,}\b"),                     # huellas en hexadecimal
    re.compile(r"(?<![\w.,])(?:19|20)\d{2}(?![\w]|[.,]\d)"),                              # años
]
MAGNITUD_EN_PALABRAS = re.compile(
    r"\b(la\s+mitad|un\s+tercio|dos\s+tercios|un\s+cuarto|tres\s+cuartos|el\s+doble|el\s+triple|la\s+(?:gran\s+)?mayor[ií]a|"
    r"la\s+minor[ií]a|casi\s+tod[oa]s?|decenas\s+de|cientos\s+de|miles\s+de(?!\s+millones))\b", re.I)

# W3 · lo que solo pueden concluir las personas
CONCLUSION = re.compile(
    r"\b(se\s+conclu\w+|conclu(?:imos|yo|ye|yen)\b|en\s+conclusi[oó]n|como\s+conclusi[oó]n|la\s+conclusi[oó]n\s+es|"
    r"demuestra(?:n)?\s+que|se\s+demuestra|queda\s+demostrad[oa]|se\s+evidencia\s+que|evidencia(?:n)?\s+que|"
    r"est[aá]\s+claro\s+que|es\s+claro\s+que|es\s+evidente|sin\s+duda|por\s+lo\s+tanto|por\s+consiguiente|en\s+consecuencia|"
    r"(?:esto|lo\s+que)\s+(?:indica|sugiere)\s+que|"
    r"se\s+recomienda\w*|recomend(?:amos|ar[ií]amos|ar[ií]a)\b|recomiendo|la\s+recomendaci[oó]n\s+es|es\s+recomendable|"
    r"deber[ií]a\w*|convendr[ií]a\w*|conviene|se\s+sugiere|sugerimos|hay\s+que|es\s+necesario|es\s+urgente|"
    r"se\s+ahorr\w*|ahorrar[ií]a\w*|reduce\s+en|reducir[ií]a\w*|mejora\s+en|mejorar[ií]a\w*|significativamente|"
    r"tiene(?:n)?\s+(?:un\s+|una\s+)?(?:gran\s+|alto\s+|bajo\s+|fuerte\s+)?impacto|impacta(?:n|r[aá])?\b|"
    r"la\s+causa\s+(?:es|fue|son|est[aá])|las\s+causas\s+(?:son|fueron)|se\s+deb(?:e|en|i[oó]|ieron)\s+a\b|debido\s+a|"
    r"es\s+causad[oa]|fue\s+causad[oa]|caus[oó]\b|provoc[oó]\b|"
    r"sobrecosto\w*|despilfarr\w*|ineficien\w*|irregularidad\w*|corrupci[oó]n)", re.I)
TITULO_DE_ANALISIS = re.compile(r"(conclusion|recomendacion|hallazgo|analisis\b)")

# W5 · lo que no se ve al leer
INVISIBLES = re.compile("[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f­​-‏‪-‮"
                        "⁠-⁩﻿\U000e0000-\U000e007f]")
ETIQUETA = re.compile(r"<\s*/?\s*([A-Za-z][\w:-]{0,30})[^<>]{0,200}>")


def leer(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def normalizar(t):
    t = "".join(ch for ch in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(ch) != "Mn")
    t = re.sub(r"^\s*\d{1,2}\s*[.)·:-]?\s*", "", t)
    t = re.sub(r"[*_`:¿?¡!]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def secciones(texto):
    """Títulos fuera de bloques de código: [(nivel, título, inicio, fin de la línea)] y cuerpos de los de nivel 2."""
    titulos, pos, en_codigo = [], 0, False
    for linea in texto.splitlines(keepends=True):
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
        elif not en_codigo:
            m = re.match(r"(#{1,6})[ \t]+(.*)", linea.rstrip("\r\n"))
            if m:
                titulos.append((len(m.group(1)), m.group(2).rstrip(" \t#"), pos, pos + len(linea)))
        pos += len(linea)
    cuerpos = []
    for i, (nivel, titulo, ini, fin) in enumerate(titulos):
        if nivel == 2:
            sig = next((t[2] for t in titulos[i + 1:] if t[0] <= 2), len(texto))
            cuerpos.append((normalizar(titulo), fin, sig))
    return titulos, cuerpos


def de_que_seccion(pos, cuerpos):
    for norm, ini, fin in cuerpos:
        if ini <= pos < fin:
            return next((nombre for nombre, patron in SECCIONES if re.match(patron, norm)), None)
    return None


# ---------------- W2 · cifras ----------------
def factor(palabra):
    for p, f in MAGNITUDES:
        if re.fullmatch(p, palabra.strip(), re.I):
            return f
    return 1.0


def interpretaciones(tok):
    """Valores posibles de una cifra escrita por una herramienta: las herramientas escriben en formato español
    (49.662) y en inglés (17,248,249,407,618.69); se aceptan las dos lecturas."""
    try:
        if len(tok) > 60:
            return set()
        if "e" in tok.lower():
            return {abs(float(tok.replace(",", ".")))}
        if tok.isdigit():
            return {float(tok)}
        if "." in tok and "," in tok:
            if tok.rfind(",") > tok.rfind("."):
                return {float(tok.replace(".", "").replace(",", "."))}
            return {float(tok.replace(",", ""))}
        sep = "." if "." in tok else ","
        partes = tok.split(sep)
        out = set()
        if 1 <= len(partes[0]) <= 3 and all(len(p) == 3 for p in partes[1:]):
            out.add(float("".join(partes)))
        if len(partes) == 2:
            out.add(float(partes[0] + "." + partes[1]))
        return out
    except (ValueError, OverflowError):
        return set()


def cifras_de_herramienta(texto):
    out = set()
    for m in CIFRA_DE_HERRAMIENTA.finditer(texto[:200_000]):
        mag = MAGNITUD.match(texto, m.end())
        f = factor(mag.group(1)) if mag else 1.0
        for v in interpretaciones(m.group(0)):
            out.update({v, v * f})
    return out


def clase_de(nombre):
    base = Path(str(nombre).split(" ")[0]).name
    return "procedencia" if base.startswith("procedencia") else "limpieza" if base.startswith("limpieza_") else base


def aprobados(artefactos):
    """Solo cuentan los artefactos verificados y aprobados; los demás se nombran, pero sus cifras no valen."""
    usados, sin_aprobar = [], []
    for nombre, datos in artefactos:
        esperado = ESTADO_APROBADO.get(clase_de(nombre))
        if isinstance(datos, dict) and esperado and datos.get("estado") == esperado:
            usados.append((nombre, datos))
        else:
            motivo = "no es un artefacto verificado" if not esperado else (
                f"estado {datos.get('estado')}" if isinstance(datos, dict) else "no se pudo leer")
            sin_aprobar.append(f"{nombre} ({motivo})")
    return usados, sin_aprobar


def pozo(artefactos):
    """Las cifras verificadas: números, cifras de los textos de las herramientas, conteos y totales del resultado."""
    P, totales = set(), []

    def agregar(v):
        try:
            v = abs(float(v))
        except (OverflowError, ValueError, TypeError):
            return
        if math.isfinite(v):
            P.add(v)

    def recorrer(x, clave, hondo=0):
        if hondo > 60 or isinstance(x, bool) or x is None:
            return
        if isinstance(x, (int, float)):
            agregar(x)
        elif isinstance(x, str):
            if clave in TEXTOS_DE_HERRAMIENTA:
                for v in cifras_de_herramienta(x):
                    agregar(v)
        elif isinstance(x, list):
            agregar(len(x))
            for v in x:
                recorrer(v, clave, hondo + 1)
        elif isinstance(x, dict):
            agregar(len(x))
            for k, v in x.items():
                if k not in SALTAR:
                    recorrer(v, k, hondo + 1)

    def es_numero(v):
        try:
            return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))
        except OverflowError:
            return False

    for nombre, datos in artefactos:
        recorrer(datos, None)
        if nombre == "informe.json":
            filas = [f for f in (datos.get("resultado_oficial") or []) if isinstance(f, dict)]
            for col in sorted({k for f in filas for k, v in f.items() if es_numero(v)}):
                t = sum(float(f[col]) for f in filas if es_numero(f.get(col)))
                totales.append((col, t))
                agregar(t)
    return sorted(P), totales


def respaldada(x, tol, P):
    tol = tol + 1e-9 * max(1.0, abs(x))
    i = bisect_left(P, x - tol)
    return i < len(P) and P[i] <= x + tol


def sin_permitidos(texto):
    t = re.sub(r"(?m)^([ \t]*#{1,6}[ \t]+)(\d{1,2}[ \t]*[.)·:-][ \t]*)", lambda m: m.group(1) + " " * len(m.group(2)), texto)
    t = re.sub(r"(?m)^([ \t]*)(\d{1,2}[.)][ \t]+)", lambda m: m.group(1) + " " * len(m.group(2)), t)   # listas numeradas
    for rx in PERMITIDOS:
        t = rx.sub(lambda m: " " * len(m.group(0)), t)
    return t


def cifras_del_texto(texto, cuerpos):
    """Cada cifra del whitepaper con su valor, su tolerancia de redondeo y si su formato es válido."""
    t = sin_permitidos(texto)
    inicios = [0] + [m.end() for m in re.finditer("\n", texto)]
    hallados = []
    for m in CIENTIFICA.finditer(t):
        dec, exp = len(m.group(2) or ""), int(m.group(3))
        if abs(exp) <= 30:
            v = float(m.group(1) + "." + (m.group(2) or "0")) * 10.0 ** exp
            hallados.append((m.start(), m.end(), m.group(0), v, 0.5 * 10.0 ** (exp - dec)))
        else:
            hallados.append((m.start(), m.end(), m.group(0), "invalida", None))
    t = CIENTIFICA.sub(lambda m: " " * len(m.group(0)), t)
    for m in TOKEN.finditer(t):
        hallados.append((m.start(), m.end(), m.group(0), None, None))
    out = []
    for ini, fin, tok, v, tol in sorted(hallados, key=lambda h: h[0]):
        c = {"cifra": tok, "linea": bisect_right(inicios, ini), "seccion": de_que_seccion(ini, cuerpos), "valida": True}
        if v == "invalida" or (v is None and not ES_NUMERO.fullmatch(tok)):
            c.update(valida=False, motivo="formato no válido: punto para miles y coma para decimales")
            out.append(c)
            continue
        if v is None:
            entero, _, dec = tok.partition(",")
            v, f = float(entero.replace(".", "") + ("." + dec if dec else "")), 1.0
            mag = MAGNITUD.match(t, fin)
            if mag:
                f = factor(mag.group(1))
                c["cifra"], fin = tok + " " + mag.group(1), mag.end()
            v, tol = v * f, 0.5 * 10.0 ** (-len(dec)) * f
        c.update(valor=v, tol=tol, porcentaje=bool(PORCENTAJE.match(t, fin)))
        if c["porcentaje"]:
            c["cifra"] += " %"
        out.append(c)
    return out


# ---------------- validación ----------------
def validar(texto, artefactos, faltan=(), utf8=True):
    """texto: el whitepaper; artefactos: [(nombre, json)] candidatos (solo cuentan los aprobados).
    Devuelve (chequeos, cifras)."""
    chequeos = []

    def chequeo(nombre, ok, detalle):
        chequeos.append({"chequeo": nombre, "ok": bool(ok), "detalle": detalle})

    if len(texto.encode("utf-8", errors="replace")) > MAX_BYTES:
        for nombre in CHEQUEOS:
            chequeo(nombre, False, f"no se revisó: el whitepaper pasa de {MAX_BYTES // 1000} KB (un whitepaper es prosa breve)")
        return chequeos, []
    lineas = texto.splitlines()
    largas = [i for i, l in enumerate(lineas, 1) if len(l) > LINEA_MAX]
    if largas:   # el resto se revisa con esas líneas recortadas: W1 ya falla
        texto = "\n".join(l[:LINEA_MAX] for l in lineas)
    titulos, cuerpos = secciones(texto)
    # W1
    problemas, posiciones = [], []
    if not texto.strip():
        problemas.append("el whitepaper está vacío")
    if not utf8:
        problemas.append("el archivo no es UTF-8 válido")
    if largas:
        problemas.append(f"{len(largas)} línea(s) de más de {LINEA_MAX} caracteres (desde la {largas[0]}): no es prosa")
    for nombre, patron in SECCIONES:
        i = next((k for k, (norm, _, _) in enumerate(cuerpos) if re.match(patron, norm)), None)
        if i is None:
            problemas.append(f"falta «{nombre}»")
            continue
        _, ini, fin = cuerpos[i]
        cuerpo = re.sub(r"(?m)^[ \t]*#{1,6}[ \t].*$", "", texto[ini:fin])
        if not re.search(r"[^\W\d_]", cuerpo):
            problemas.append(f"«{nombre}» está vacía")
        posiciones.append(i)
    if posiciones != sorted(posiciones):
        problemas.append("las secciones no van en el orden de la ficha")
    chequeo(CHEQUEOS[0], not problemas, "; ".join(problemas) or f"las {len(SECCIONES)} secciones, en orden y con contenido")

    # W2
    usados, sin_aprobar = aprobados(artefactos)
    P, totales = pozo(usados)
    cifras = cifras_del_texto(texto, cuerpos)
    for c in cifras:
        c["respaldada"] = c["valida"] and (respaldada(c["valor"], c["tol"], P) or (
            c["porcentaje"] and respaldada(c["valor"] / 100, c["tol"] / 100, P)))
    problemas = []
    if not any(n == "informe.json" for n, _ in usados):
        problemas.append("no hay cifra verificada: informe.json falta o no está aprobado")
    malas = [c for c in cifras if not c["respaldada"]]
    if malas:
        problemas.append(f"{len(malas)} cifra(s) sin respaldo en los artefactos verificados: " + "; ".join(
            f"«{c['cifra'][:30]}» (línea {c['linea']}{', ' + c['motivo'] if c.get('motivo') else ''})" for c in malas[:8]))
    palabras = sorted({re.sub(r"\s+", " ", m.group(0).lower()) for m in MAGNITUD_EN_PALABRAS.finditer(texto)})
    if palabras:
        problemas.append("magnitudes con palabras que no se pueden comprobar: " + ", ".join(f"«{p}»" for p in palabras[:6]))
    if totales:
        en_cifra = [c for c in cifras if c["seccion"] == CIFRA and c["valida"]]
        if not any(abs(c["valor"] - t) <= c["tol"] + 1e-9 * max(1.0, abs(t)) for c in en_cifra for _, t in totales):
            problemas.append(f"«{CIFRA}» no cita ningún total del resultado aprobado ({', '.join(col for col, _ in totales)})")
    nota = (f" · artefactos: {', '.join(n for n, _ in usados) or 'ninguno'}"
            + (f" · no cuentan: {', '.join(sin_aprobar)}" if sin_aprobar else "")
            + (f" · no están: {', '.join(faltan)}" if faltan else ""))
    chequeo(CHEQUEOS[1], not problemas,
            ("; ".join(problemas) if problemas else f"{len(cifras)} cifra(s), todas en los artefactos verificados") + nota)

    # W3
    plano = re.sub(r"\s+", " ", texto)
    frases = sorted({re.sub(r"\s+", " ", m.group(0).lower()) for m in CONCLUSION.finditer(plano)})
    malos_titulos = [t for _, t, _, _ in titulos if TITULO_DE_ANALISIS.match(normalizar(t))
                     and not re.match(SECCIONES[7][1], normalizar(t))]
    problemas = []
    if frases:
        problemas.append("frases de conclusión, recomendación, causa o juicio: " + ", ".join(f"«{f[:40]}»" for f in frases[:6]))
    if malos_titulos:
        problemas.append("títulos de análisis: " + ", ".join(f"«{t[:40]}»" for t in malos_titulos[:3]))
    chequeo(CHEQUEOS[2], not problemas, "; ".join(problemas) or "describe lo hecho y lo medido; el análisis queda para las personas")

    # W4
    sec = next(((ini, fin) for norm, ini, fin in cuerpos if re.match(SECCIONES[7][1], norm)), None)
    problemas, tipos, items = [], set(), []
    if sec:
        for linea in texto[sec[0]:sec[1]].splitlines():
            m = re.match(r"\s*(?:[-*+]|\d{1,2}[.)])\s+(.*)", linea)
            if m:
                items.append(m.group(1).strip())
    for k, it in enumerate(items, 1):
        if "¿" not in it or "?" not in it or it.find("¿") > it.rfind("?"):
            problemas.append(f"la pregunta {k} no lleva «¿» y «?»")
        tipo = re.match(r"(costo|calidad|impacto)\b", normalizar(it))
        if tipo:
            tipos.add(tipo.group(1))
        else:
            problemas.append(f"la pregunta {k} no empieza con su tipo (Costo, Calidad o Impacto)")
    if len(items) < 3:
        problemas.append(f"hay {len(items)} pregunta(s); se piden al menos 3")
    faltan_tipos = [t for t in TIPOS if t not in tipos]
    if faltan_tipos:
        problemas.append(f"falta al menos una pregunta de: {', '.join(faltan_tipos)}")
    chequeo(CHEQUEOS[3], not problemas, "; ".join(problemas[:6]) or f"{len(items)} preguntas, de costo, calidad e impacto")

    # W5 (sobre el texto con los espacios colapsados: así ningún patrón se traba con miles de espacios seguidos)
    problemas = []
    comentarios = plano.count("<!--")
    if comentarios <= 50 and parece_instruccion(plano):
        problemas.append("trae un texto con forma de instrucción para una IA (no se copia aquí)")
    for nombre, rx in PATRONES.items():
        if nombre == "correo":   # solo alrededor de cada «@»: sin «@» no hay correo, y así no hay retroceso cuadrático
            hallados = sorted({x.group(0) for m in re.finditer("@", plano)
                               for x in rx.finditer(plano[max(0, m.start() - 80):m.end() + 260])})
        else:
            hallados = [m.group(0) for m in rx.finditer(plano)]
        if hallados:
            problemas.append(f"{nombre}: {len(hallados)} ({enmascarar(hallados[0])})")
    if comentarios:
        problemas.append("comentario HTML (texto que no se ve al leer)")
    invisibles = INVISIBLES.findall(texto)
    if invisibles:
        problemas.append(f"{len(invisibles)} carácter(es) invisibles o de control (p. ej. U+{ord(invisibles[0]):04X})")
    etiquetas = sorted({m.group(1).lower() for m in ETIQUETA.finditer(texto)})
    if etiquetas:
        problemas.append("marcado HTML: " + ", ".join(etiquetas[:5]))
    chequeo(CHEQUEOS[4], not problemas, "; ".join(problemas) or "ninguno")
    return chequeos, cifras


class _Tiempo(Exception):
    pass


def _alarma(*_):
    raise _Tiempo()


def validar_con_tope(texto, artefactos, faltan=(), utf8=True, tope=TIEMPO_MAX):
    """validar() con un tope de tiempo: si un texto hecho para trabar las expresiones regulares lo excede, falla cerrado."""
    usar = hasattr(signal, "SIGALRM")
    if usar:
        anterior = signal.signal(signal.SIGALRM, _alarma)
        signal.alarm(tope)
    try:
        return validar(texto, artefactos, faltan, utf8)
    except _Tiempo:
        return [{"chequeo": "W0 la validación termina a tiempo", "ok": False,
                 "detalle": f"tardó más de {tope} s: el whitepaper no parece prosa (posible ataque de rendimiento)"}], []
    finally:
        if usar:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, anterior)


def procedencias(c):
    """Las procedencias de la ingesta: en la corrida, en datos/ o junto al dato crudo (como en informe_final.py)."""
    from rutas import resolver
    candidatos = sorted(c.glob("procedencia*.json")) + sorted((c / "datos").glob("procedencia*.json"))
    spec = leer(c / "spec.json") or {}
    for r in list((spec.get("datos_crudos") or {}).values()) + list((spec.get("datos") or {}).values()):
        candidatos += sorted(Path(resolver(r)).parent.glob("procedencia*.json"))
    vistas, out = set(), []
    for p in candidatos:
        real = p.resolve()
        if real in vistas or not p.is_file():
            continue
        vistas.add(real)
        try:
            nombre = str(real.relative_to(c.resolve()))
        except ValueError:
            nombre = f"{p.name} (junto al dato crudo)"
        out.append((nombre, p))
    return out


def artefactos_de(c):
    """Los artefactos candidatos de una corrida [(nombre, json)] y los que no están."""
    candidatos, faltan = [], []
    for nombre in ("informe.json", "gobernanza.json", "grafico_verificacion.json"):
        if (c / nombre).exists():
            candidatos.append((nombre, leer(c / nombre)))
        else:
            faltan.append(nombre)
    procs = procedencias(c)
    candidatos += [(nombre, leer(p)) for nombre, p in procs]
    limpiezas = sorted(c.glob("limpieza_*.json"))
    candidatos += [(p.name, leer(p)) for p in limpiezas]
    faltan += (["procedencia*.json"] if not procs else []) + (["limpieza_*.json"] if not limpiezas else [])
    return candidatos, faltan


def validar_corrida(c):
    ruta = c / "whitepaper.md"
    if ruta.exists():
        crudo = ruta.read_bytes()
        try:
            texto, utf8 = crudo.decode("utf-8"), True
        except UnicodeDecodeError:
            texto, utf8 = crudo.decode("utf-8", errors="replace"), False
        candidatos, faltan = artefactos_de(c)
        chequeos, cifras = validar_con_tope(texto, candidatos, faltan, utf8)
        huella = hashlib.sha256(crudo).hexdigest()
    else:
        chequeos, cifras, huella = [{"chequeo": "W0 existe whitepaper.md", "ok": False,
                                     "detalle": "el documentador no escribió whitepaper.md"}], [], None
    fallas = [x for x in chequeos if not x["ok"]]
    out = {"whitepaper": "whitepaper.md", "sha256": huella, "estado": "aprobado" if not fallas else "revisar",
           "chequeos": chequeos,
           "cifras": [{k: x[k] for k in ("cifra", "linea", "seccion", "respaldada") if k in x} for x in cifras[:400]]}
    (c / "whitepaper_verificacion.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in chequeos:
        print(f"  {'✓' if x['ok'] else '✗'} {x['chequeo']}: {x['detalle']}")
    print("RESUMEN " + json.dumps({"estado": out["estado"], "chequeos": len(chequeos), "fallas": len(fallas),
                                   "cifras": len(cifras)}, ensure_ascii=False))
    return 1 if fallas else 0


# ---------------- autoprueba ----------------
def autoprueba():
    """Whitepapers ficticios buenos y malos (sin red ni archivos de una corrida): cada chequeo atrapa lo suyo."""
    informe = {"estado": "aprobado", "preguntas_abiertas": 1,
               "resultado_oficial": [{"region": "Norte", "ventas_netas": 1250000.5}, {"region": "Sur", "ventas_netas": 830000.0},
                                     {"region": "Centro", "ventas_netas": 419999.5}],
               "reglas": [{"id": f"R{i}"} for i in range(1, 5)],
               "implementaciones": {"a": {"conciliacion": {"filas_leidas": 1520, "usadas": 1508, "excluidas": {"anulada": 12}},
                                          "reglas": [{"id": "R1", "mensaje": "resultado 2,500,000.00 · fuente 2,500,000.00"}],
                                          "caso_conocido": {"obtenido": [{"region": "Norte", "ventas_netas": 4321.0}]}}},
               "anticipo": {"minimo": 2000000, "maximo": 3000000, "total": 2500000.0,
                            "razon": "Se esperan unas 7.777 facturas y entre 2 y 3 millones."}}
    procedencia = {"estado": "aprobada", "filas": 1520, "conteo_fuente": 1520, "licencia": "CC BY-SA 4.0",
                   "consultado_legible": "06-11-2026 05:29", "cita": "Ventas ficticias, consultado el 06-11-2026. 1.520 filas."}
    limpieza = {"estado": "aprobada", "filas": 1520, "filas_ok": 1490, "marcas": {"anulada": 12, "atipico": 18},
                "calidad_despues": {"valor": {"completitud": 0.98}},
                "pruebas": [{"prueba": "filas marcadas «atipico» ≤ 40", "ok": True, "detalle": "18"}]}
    gobernanza = {"estado": "aprobado", "tablas": {"ventas": {"filas": 1520}}, "k_anonimato": {"aplica": False},
                  "custodio": {"hay_custodio": True, "columnas_fuente": 9, "ia_no_vio": []}, "problemas": []}
    grafico = {"estado": "aprobado", "comprobaciones": [
        {"comprobacion": "cuenta de control", "ok": True, "detalle": "gráfico 2,500,000.00 + fuera 0.00 · tabla 2,500,000.00"},
        {"comprobacion": "título", "ok": True, "detalle": "Ventas netas por región: 3 regiones, 2,5 millones; Norte 50,0 %"}]}
    base = [("informe.json", informe), ("procedencia_ventas.json", procedencia), ("limpieza_ventas.json", limpieza),
            ("gobernanza.json", gobernanza), ("grafico_verificacion.json", grafico)]
    pregunta = "## Pregunta\n¿Cuánto vendió cada región en el primer semestre de 2026, en ventas netas?\n\n"
    bueno = "# Whitepaper · Ventas netas por región (ejemplo ficticio)\n\n" \
            "Resumen de lo desarrollado, para que las personas hagan el análisis.\n\n" + pregunta + """## Datos y procedencia
Ventas ficticias consultadas el 06-11-2026 05:29: 1.520 filas, igual al conteo de la fuente. Licencia CC BY-SA 4.0; la huella SHA-256 del archivo está en la procedencia.

## Limpieza
De 1.520 filas, 1.490 quedaron sin marcas: 12 facturas anuladas (se excluyen) y 18 valores atípicos (solo avisan). Nada se borró.

## Cifra verificada y cómo se verificó
Ventas netas del semestre: 2.500.000 pesos (2,5 millones) en 3 regiones. Dos implementaciones independientes dieron lo mismo y pasaron las 4 reglas (R1 a R4); la conciliación cierra: 1.520 filas leídas = 1.508 usadas + 12 excluidas.

## Gráfico
Barras desde cero con las 3 regiones; según el título, la región Norte suma el 50,0 %. Ver [grafico.html](grafico.html).

## Gobernanza
El barrido no encontró datos personales. El custodio clasificó las 9 columnas de la fuente; el k-anonimato no aplica porque el resultado solo publica agregados (Ley 1581 de 2012).

## Límites
Queda 1 pregunta abierta (P1): la cifra usa su valor por defecto.

## Preguntas para el análisis de las personas
- **Costo.** ¿Qué parte de las ventas netas se va en devoluciones en cada región?
- **Calidad.** ¿Qué tienen en común las 18 facturas con valores atípicos?
- **Impacto.** ¿A qué clientes y municipios llegan las ventas de cada región?
"""
    limites = "Queda 1 pregunta abierta (P1): la cifra usa su valor por defecto."
    impacto = "- **Impacto.** ¿A qué clientes y municipios llegan las ventas de cada región?\n"
    casos = []

    def caso(nombre, esperado, reemplazos=(), artefactos=None, texto=None):
        texto = bueno if texto is None else texto
        for viejo, nuevo in reemplazos:
            if viejo not in texto:
                raise SystemExit(f"autoprueba mal armada en «{nombre}»: no está {viejo!r}")
            texto = texto.replace(viejo, nuevo, 1)
        casos.append((nombre, texto, base if artefactos is None else artefactos, esperado))

    def mas(frase):
        return [(limites, limites + " " + frase)]

    caso("whitepaper bueno", set())
    caso("redondeo bien hecho y porcentaje de una fracción", set(),
         mas("El total, redondeado, es de 2,50 millones; la completitud del valor quedó en el 98 %."))
    caso("falta una sección", {"W1"}, [("## Gráfico\n", "## Figura\n")])
    caso("sección vacía", {"W1"}, [(limites, "")])
    caso("secciones fuera de orden", {"W1"}, [(pregunta, ""), ("## Preguntas para", pregunta + "## Preguntas para")])
    caso("línea que no es prosa", {"W1"}, mas("x" * (LINEA_MAX + 1)))
    caso("cifra inventada", {"W2"}, mas("Hay 3.217 clientes en la base."))
    caso("cifra de la prosa de la IA (razón del anticipo)", {"W2"}, mas("Se esperaban unas 7.777 facturas."))
    caso("cifra del caso conocido (datos ficticios)", {"W2"}, mas("El caso conocido dio 4.321 pesos."))
    caso("redondeo mal hecho", {"W2"}, [("(2,5 millones)", "(2,6 millones)")])
    caso("formato en inglés", {"W2"}, [("2.500.000 pesos", "2,500,000 pesos")])
    caso("porcentaje inventado", {"W2"}, [("suma el 50,0 %", "suma el 55 %")])
    caso("notación científica enorme", {"W2"}, mas("Escala 1e9999."))
    caso("magnitud con palabras", {"W2"}, mas("La mitad de las ventas sale del Norte."))
    caso("la cifra verificada no cita el total", {"W2"},
         [("Ventas netas del semestre: 2.500.000 pesos (2,5 millones) en 3 regiones.", "Ventas netas del semestre en 3 regiones.")])
    caso("informe sin aprobar: no hay cifra verificada", {"W2"},
         artefactos=[("informe.json", {**informe, "estado": "revisar"})] + base[1:])
    caso("gobernanza sin aprobar: sus cifras no cuentan", {"W2"},
         artefactos=base[:3] + [("gobernanza.json", {**gobernanza, "estado": "revisar"})] + base[4:])
    caso("un archivo que no es artefacto verificado no cuenta", {"W2"}, mas("El gráfico deja 38 entidades en «Otras»."),
         artefactos=base + [("grafico.json", {"estado": "aprobado", "otras": {"entidades": 38}})])
    caso("conclusión", {"W3"}, mas("Esto demuestra que el Norte vende mejor."))
    caso("recomendación", {"W3"}, mas("Se recomienda cerrar la región Centro."))
    caso("«debería»", {"W3"}, mas("La región Sur debería vender más."))
    caso("causa", {"W3"}, mas("La diferencia se debe a la temporada."))
    caso("ahorro", {"W3"}, mas("Con menos devoluciones se ahorra dinero."))
    caso("título de conclusiones", {"W3"}, [("## Límites\n", "## Conclusiones\nSin conclusiones.\n\n## Límites\n")])
    caso("menos de tres preguntas", {"W4"}, [("- **Calidad.** ¿Qué tienen en común las 18 facturas con valores atípicos?\n", "")])
    caso("pregunta sin signos", {"W4"}, [("¿Qué parte de las ventas netas se va en devoluciones en cada región?",
                                          "Qué parte de las ventas netas se va en devoluciones en cada región.")])
    caso("falta un tipo de pregunta", {"W4"}, [("- **Impacto.** ¿A qué", "- **Costo.** ¿A qué")])
    caso("pregunta sin rótulo de tipo", {"W4"},
         [(impacto, impacto.replace("**Impacto.** ", "") + "- **Impacto.** ¿Cómo cambia la llegada por municipio?\n")])
    caso("dato personal", {"W5"}, mas("Dudas: " + "ana.perez" + "@" + "ejemplo.invalid" + "."))
    caso("comentario HTML", {"W5"}, mas("<!-- nota interna -->"))
    caso("carácter invisible", {"W5"}, [("valor por defecto", "valor por" + "​" + " defecto")])
    caso("marcado HTML", {"W5"}, mas("<span>texto</span>"))
    caso("más de 200 KB: no se revisa y falla", {"W1", "W2", "W3", "W4", "W5"}, texto=bueno + ("Relleno. " * 30_000))
    errores = 0
    for nombre, texto, artefactos, esperado in casos:
        chequeos, _ = validar(texto, artefactos)
        obtenido = {x["chequeo"].split()[0] for x in chequeos if not x["ok"]}
        ok = obtenido == esperado
        errores += not ok
        print(f"  {'✓' if ok else '✗'} {nombre}: " + ("pasa" if not obtenido else "atrapado por " + ", ".join(sorted(obtenido)))
              + ("" if ok else f" (se esperaba {', '.join(sorted(esperado)) or 'que pasara'}) · "
                 + " | ".join(x["detalle"][:200] for x in chequeos if not x["ok"])))
    # cada texto-instrucción de la batería de inyección, puesto en el whitepaper, lo atrapa W5
    maliciosos = [l for l in (AQUI.parent / "baterias" / "inyeccion" / "maliciosos.txt").read_text(encoding="utf-8").splitlines()
                  if l.strip()]
    no_atrapados = 0
    for linea in maliciosos:
        chequeos, _ = validar(bueno.replace(limites, limites + "\n\n" + linea), base)
        no_atrapados += not any(x["chequeo"].startswith("W5") and not x["ok"] for x in chequeos)
    errores += bool(no_atrapados or not maliciosos)
    print(f"  {'✓' if maliciosos and not no_atrapados else '✗'} textos-instrucción de baterias/inyeccion: W5 atrapa "
          f"{len(maliciosos) - no_atrapados} de {len(maliciosos)}")
    # textos hechos para trabar las expresiones regulares: todos terminan rápido (nunca cuelgan el pipeline), y los
    # que traen algo que las reglas rechazan, fallan
    hostiles = [("cifras pegadas", "1." * 2_000, True),
                ("cédula con miles de espacios", "cédula" + " " * 1_990 + ":" + " " * 1_990 + "1", False),
                ("línea larga de espacios", "cc" + " " * 9_000 + "1", True),
                ("puntos sin arroba", ("a." * 1_900 + "\n") * 40, False),
                ("puntos con una arroba al final", ("1." * 1_900 + "@\n") * 40, False),
                ("comentarios sin cerrar", "<!--" * 999, True),
                ("etiquetas sin cerrar", ("<a " + "x" * 190 + "\n") * 300, False)]
    malos = []
    for nombre, relleno, debe_fallar in hostiles:
        t0 = time.perf_counter()
        chequeos, _ = validar_con_tope(bueno.replace(limites, limites + "\n\n" + relleno), base, tope=20)
        seg = time.perf_counter() - t0
        if seg > 10 or (debe_fallar and all(x["ok"] for x in chequeos)):
            malos.append(f"{nombre} ({seg:.1f} s)")
    errores += bool(malos)
    print(f"  {'✓' if not malos else '✗'} textos hostiles: los {len(hostiles)} terminan en menos de 10 s"
          + (f" · no: {', '.join(malos)}" if malos else ""))
    print("RESUMEN " + json.dumps({"autoprueba": len(casos) + 2, "errores": errores}))
    return 1 if errores else 0


def main(argv):
    if argv[:1] == ["--autoprueba"]:
        return autoprueba()
    if not argv:
        raise SystemExit(__doc__)
    return validar_corrida(Path(argv[0]).resolve())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
