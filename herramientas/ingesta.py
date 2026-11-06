#!/usr/bin/env python3
"""Ingesta con contrato de datos (sin IA): lee la fuente, prueba la carga y deja la procedencia.

Uso: python ingesta.py contrato_datos.json --salida <carpeta> [--repetir]

El contrato de datos (el «lector» que escribe la IA y revisa una persona) declara:
  fuente:   {tipo: "socrata", dominio, conjunto, titulo, filtro, filtro_legible, licencia, atribucion, unidad}
            o {tipo: "local", ruta, titulo, licencia, atribucion, unidad, conteo (opcional: filas que declara quien
            entrega el archivo; si no lo dice, se cuentan aparte, con otro método que el del lector)}
  tabla, llave, columnas: {columna: "texto" | "entero" | "decimal" | "fecha"}
  dominios: {columna: [valores]}        duros: si un valor no está, la carga se rechaza
  rangos:   {columna: [min, max]}       duros (fechas como "aaaa-mm-dd")
  avisos:   {columna: [min, max]}       blandos: se cuentan y se reportan (R7), no se corrigen
  personales_justificadas: {columna: motivo}   sin esto, una columna personal, cuasi-identificadora o de texto libre
                                               (por su nombre o por su descripción en los metadatos) se rechaza
  base_legal_sensibles: {columna: base legal}  sin esto, un dato sensible (origen étnico, salud o discapacidad, vida
                                               sexual, biométricos, convicciones, menores: Ley 1581, art. 5 y 7) se rechaza

Pruebas de cada carga (R15 del curso): conteo contra la fuente, llave única, llave sin nulos,
rangos y dominios; además, tipos declarados como FAILFAST (R11), columnas que existen en la fuente
(«el esquema desmiente la columna inventada») y minimización de datos personales.
La escritura es atómica y repetible (R12): con la fuente igual, correr dos veces deja el mismo archivo.
"""
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gobernanza import clasificar_columna, enmascarar, es_sensible  # noqa: E402
from reglas_base import contar_registros, leer_tabla  # noqa: E402

PAGINA = 50000
AGENTE = {"User-Agent": "agente-solicitudes (analisis de datos abiertos)"}


def pedir(url, intentos=3):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=AGENTE), timeout=300) as r:
                return r.read().decode("utf-8")
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(3 * (i + 1))


def minimizacion(contrato, columnas, descripciones=None):
    """Minimización (D7 y Ley 1581 de 2012): sin justificación escrita no entra una columna personal, cuasi-identificadora
    o de texto libre (por su nombre o por su descripción en los metadatos), y un dato sensible además necesita la base
    legal registrada en el contrato (base_legal_sensibles). Devuelve None o el rechazo."""
    descripciones = descripciones or {}
    justificadas = contrato.get("personales_justificadas", {})
    bases = contrato.get("base_legal_sensibles", {})
    sensibles = [c for c in columnas if es_sensible(c, descripciones.get(c))]
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


def socrata(fuente, columnas, llave, meta=None):
    base = f"https://{fuente['dominio']}"
    meta = meta or json.loads(pedir(f"{base}/api/views/{fuente['conjunto']}.json"))
    existen = {c["fieldName"] for c in meta.get("columns", [])}
    inventadas = [c for c in columnas if c not in existen]
    if inventadas:
        return None, None, None, f"columnas que no existen en la fuente: {inventadas}", {}
    q = lambda p: urllib.parse.urlencode({"$" + k: v for k, v in p.items()})
    contar = lambda: int(json.loads(pedir(f"{base}/resource/{fuente['conjunto']}.json?"
                                          + q({"select": "count(*) AS n", "where": fuente["filtro"]})))[0]["n"])
    for _ in range(2):
        antes = contar()
        filas, off = [], 0
        while True:
            txt = pedir(f"{base}/resource/{fuente['conjunto']}.csv?" + q({
                "select": ",".join(columnas), "where": fuente["filtro"], "order": llave,
                "limit": str(PAGINA), "offset": str(off)}))
            lector = list(csv.reader(io.StringIO(txt), strict=True))
            if lector and lector[0] != columnas:
                return None, None, None, f"la fuente devolvió columnas distintas: {lector[0]}", {}
            filas += lector[1:]
            if len(lector) - 1 < PAGINA:
                break
            off += PAGINA
        despues = contar()
        if antes == despues:
            url = f"{base}/resource/{fuente['conjunto']}.csv?" + q({"select": ",".join(columnas), "where": fuente["filtro"]})
            return filas, despues, url, None, {"conteo_de": "count(*) de la API, el mismo antes y después de descargar"}
    # FAILFAST: con la fuente cambiando no hay una carga que defender; nada se aprueba con una nota
    return None, None, None, "la fuente cambió mientras se descargaba (dos veces); vuelva a correr", {}


def local(fuente, columnas):
    """CSV local con el mismo lector estricto de las reglas (reglas_base.leer_tabla): una fila con más o menos campos,
    una línea vacía o una comilla sin cerrar rechazan la carga con su número de línea; nada se rellena ni se recorta.
    El conteo de la fuente sale aparte: el que declara el contrato (fuente.conteo) o los saltos de línea fuera de
    comillas, que es otra cuenta, no la del mismo lector."""
    ruta = Path(fuente["ruta"])
    texto = ruta.read_text(encoding="utf-8-sig")
    try:
        cab, cuerpo, _ = leer_tabla(texto, f"de {ruta.name}")
    except ValueError as e:
        return None, None, None, str(e), {}
    faltan = [c for c in columnas if c not in cab]
    if faltan:
        return None, None, None, f"columnas que no existen en el archivo: {faltan}", {}
    idx = [cab.index(c) for c in columnas]
    filas = [[f[i] for i in idx] for f in cuerpo]
    if fuente.get("conteo") is not None:
        conteo, de_donde = int(fuente["conteo"]), "el que declara el contrato (fuente.conteo)"
    else:
        conteo, de_donde = contar_registros(texto), "contado aparte: saltos de línea fuera de comillas"
    lineas = texto.count("\n") - 1
    nota = None if lineas == len(cuerpo) else (
        f"el archivo tiene {lineas} líneas y {len(cuerpo)} registros: hay saltos de línea dentro de campos "
        "(se leyó respetando las comillas, como multiLine=True)")
    return filas, conteo, str(ruta.resolve()), nota, {"conteo_de": de_donde}


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


def probar(contrato, columnas, filas, conteo_fuente, conteo_de=None):
    tipos = contrato["columnas"]
    llave = contrato["llave"]
    ik = columnas.index(llave)
    pruebas, avisos, nulos = [], [], {}
    pruebas.append({"prueba": "conteo contra la fuente", "ok": len(filas) == conteo_fuente,
                    "detalle": f"filas leídas {len(filas)} · conteo de la fuente {conteo_fuente}"
                              + (f" ({conteo_de})" if conteo_de else "")})
    llaves = [f[ik].strip() for f in filas]
    vacias = sum(1 for k in llaves if not k)
    repetidas = len(llaves) - len(set(llaves))
    pruebas.append({"prueba": "llave única", "ok": repetidas == 0, "detalle": f"{llave}: {repetidas} repetidas"})
    pruebas.append({"prueba": "llave sin nulos", "ok": vacias == 0, "detalle": f"{llave}: {vacias} vacías"})
    fallas_tipo, fuera_rango, fuera_dominio, conteo_avisos = {}, {}, {}, {}
    for j, col in enumerate(columnas):
        tipo = tipos[col]
        personal = clasificar_columna(col) == "personal" or es_sensible(col)
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
                    e["ejemplos"].append(enmascarar(v) if personal else v[:40])
                continue
            if dom and v not in dom:
                fuera_dominio.setdefault(col, set()).add(enmascarar(v) if personal else v[:40])
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


def miles(n):
    return f"{n:,}".replace(",", ".")


def ingerir(ruta_contrato, salida, repetir=False):
    contrato = json.loads(Path(ruta_contrato).read_text(encoding="utf-8"))
    fuente, tabla, llave = contrato["fuente"], contrato["tabla"], contrato["llave"]
    columnas = list(contrato["columnas"])
    if llave not in columnas:
        raise SystemExit(f"La llave {llave} no está entre las columnas declaradas")
    justificadas = contrato.get("personales_justificadas", {})
    meta = None
    if fuente["tipo"] == "socrata":   # la descripción de cada columna también cuenta: el nombre puede esconder lo que es
        meta = json.loads(pedir(f"https://{fuente['dominio']}/api/views/{fuente['conjunto']}.json"))
    descripciones = {c.get("fieldName"): c.get("description") or "" for c in (meta or {}).get("columns", [])}
    rechazo = minimizacion(contrato, columnas, descripciones)
    if rechazo:
        for linea in rechazo["lineas"]:
            print(f"✗ minimización: {linea}")
        print(f"Ingesta rechazada: {rechazo['motivo']}")
        print("RESUMEN " + json.dumps({"estado": "rechazada", "motivo": rechazo["motivo"], "columnas": rechazo["columnas"]},
                                      ensure_ascii=False))
        return 1
    leer = (lambda: socrata(fuente, columnas, llave, meta)) if fuente["tipo"] == "socrata" else (lambda: local(fuente, columnas))
    filas, conteo_fuente, origen, nota, extra = leer()
    if filas is None:
        print(f"Ingesta rechazada: {nota}")
        print("RESUMEN " + json.dumps({"estado": "rechazada", "motivo": nota}, ensure_ascii=False))
        return 1
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(columnas)
    w.writerows(filas)
    contenido = buf.getvalue().encode("utf-8")
    huella = hashlib.sha256(contenido).hexdigest()
    destino = salida / f"{tabla}.csv"
    anterior = hashlib.sha256(destino.read_bytes()).hexdigest() if destino.exists() else None
    repetible = None
    if repetir:
        filas2 = leer()[0]
        b2 = io.StringIO()
        w2 = csv.writer(b2, lineterminator="\n")
        w2.writerow(columnas)
        w2.writerows(filas2 or [])
        repetible = hashlib.sha256(b2.getvalue().encode("utf-8")).hexdigest() == huella
    if anterior != huella:
        fd, tmp = tempfile.mkstemp(dir=salida, suffix=".tmp")
        with os.fdopen(fd, "wb") as fh:
            fh.write(contenido)
        os.replace(tmp, destino)     # escritura atómica: reemplaza, nunca agrega (R12)
    pruebas, avisos, nulos = probar(contrato, columnas, filas, conteo_fuente, extra.get("conteo_de"))
    if repetible is not None:
        pruebas.append({"prueba": "correr dos veces da lo mismo", "ok": repetible,
                        "detalle": "la segunda lectura dio el mismo archivo, byte a byte" if repetible
                        else "la segunda lectura dio otro archivo"})
    ahora = datetime.now()
    unidad = fuente.get("unidad", "filas")
    if fuente["tipo"] == "socrata":
        cita = (f"{fuente['titulo']}, {fuente['dominio'].replace('www.', '')} ({fuente['conjunto']}), "
                f"{fuente.get('filtro_legible') or fuente['filtro']}, consultado el {ahora:%d-%m-%Y}. {miles(len(filas))} {unidad}.")
    else:
        cita = f"{fuente['titulo']}, archivo {Path(fuente['ruta']).name}, leído el {ahora:%d-%m-%Y}. {miles(len(filas))} {unidad}."
    proc = {
        "tabla": tabla, "archivo": str(destino), "fuente": fuente, "origen": origen, "llave": llave,
        "columnas": contrato["columnas"], "consultado": ahora.isoformat(timespec="seconds"),
        "consultado_legible": f"{ahora:%d-%m-%Y %H:%M}", "filas": len(filas), "conteo_fuente": conteo_fuente,
        "sha256": huella, "sha256_anterior": anterior, "sin_cambios": anterior == huella,
        "nulos": nulos, "avisos": avisos, "nota": nota, "pruebas": pruebas, "cita": cita,
        "licencia": fuente.get("licencia"), "atribucion": fuente.get("atribucion"),
        "columnas_personales_justificadas": justificadas, "base_legal_sensibles": contrato.get("base_legal_sensibles", {}),
    }
    proc["estado"] = "aprobada" if all(p["ok"] for p in pruebas) else "rechazada"
    for nombre in (f"procedencia_{tabla}.json", "procedencia.json"):
        (salida / nombre).write_text(json.dumps(proc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ingesta {proc['estado']}: {miles(len(filas))} {unidad} → {destino}")
    for p in pruebas:
        print(f"  {'✓' if p['ok'] else '✗'} {p['prueba']}: {p['detalle']}")
    for a in avisos:
        print(f"  · aviso: {a}")
    if nota:
        print(f"  · nota: {nota}")
    print(f"  · nulos: {nulos}")
    print(f"  · {'sin cambios frente a la carga anterior' if proc['sin_cambios'] else 'archivo escrito'} · sha256 {huella[:16]}…")
    print(f"  · cita: {cita}")
    print("RESUMEN " + json.dumps({"estado": proc["estado"], "filas": len(filas), "conteo_fuente": conteo_fuente,
                                   "fallas": [p["prueba"] for p in pruebas if not p["ok"]]}, ensure_ascii=False))
    return 0 if proc["estado"] == "aprobada" else 1


def main(argv):
    if len(argv) < 3 or "--salida" not in argv:
        raise SystemExit(__doc__)
    salida = argv[argv.index("--salida") + 1]
    return ingerir(argv[0], salida, repetir="--repetir" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
