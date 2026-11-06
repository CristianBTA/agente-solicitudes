#!/usr/bin/env python3
"""Ingesta con contrato de datos (sin IA): lee la fuente, prueba la carga y deja la procedencia.

Uso: python ingesta.py contrato_datos.json --salida <carpeta> [--repetir]
     python ingesta.py --autoprueba     prueba sin red, con un Socrata falso, que la procedencia reproduce la carga

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
import shutil
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gobernanza import clasificar_columna, enmascarar, es_sensible  # noqa: E402
from reglas_base import contar_registros, leer_tabla  # noqa: E402

PAGINA = 50000
RAIZ = Path(__file__).resolve().parent.parent
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
    recurso = f"{base}/resource/{fuente['conjunto']}.csv?"
    for _ in range(2):
        antes = contar()
        filas, off, paginas = [], 0, []
        while True:
            paginas.append(recurso + q({"select": ",".join(columnas), "where": fuente["filtro"], "order": llave,
                                        "limit": str(PAGINA), "offset": str(off)}))
            lector = list(csv.reader(io.StringIO(pedir(paginas[-1])), strict=True))
            if lector and lector[0] != columnas:
                return None, None, None, f"la fuente devolvió columnas distintas: {lector[0]}", {}
            filas += lector[1:]
            if len(lector) - 1 < PAGINA:
                break
            off += PAGINA
        despues = contar()
        if antes == despues:
            # la consulta EXACTA: con su orden y su tamaño; sin $order la fuente devuelve otro orden y sin $limit, 1.000 filas
            consulta = {"select": ",".join(columnas), "where": fuente["filtro"], "order": llave, "limit_por_pagina": PAGINA,
                        "paginas": len(paginas)}
            origen = recurso + q({"select": ",".join(columnas), "where": fuente["filtro"], "order": llave, "limit": str(despues)})
            return filas, despues, origen, None, {"conteo_de": "count(*) de la API, el mismo antes y después de descargar",
                                                  "consulta": consulta, "paginas": paginas, "version_fuente": version_fuente(meta)}
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
    return filas, conteo, portable(ruta), nota, {"conteo_de": de_donde}


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


def retirar(salida, tabla, motivo, escribir=True):
    """Una carga rechazada no deja datos donde los leen las etapas siguientes: si había un <tabla>.csv de una carga
    anterior, se retira y se dice; y queda la procedencia de esta carga en «rechazada» (nunca la aprobada de antes)."""
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
        retirar(salida, tabla, rechazo["motivo"])
        print("RESUMEN " + json.dumps({"estado": "rechazada", "motivo": rechazo["motivo"], "columnas": rechazo["columnas"]},
                                      ensure_ascii=False))
        return 1
    leer = (lambda: socrata(fuente, columnas, llave, meta)) if fuente["tipo"] == "socrata" else (lambda: local(fuente, columnas))
    filas, conteo_fuente, origen, nota, extra = leer()
    if filas is None:
        print(f"Ingesta rechazada: {nota}")
        retirar(salida, tabla, nota)
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
    pruebas, avisos, nulos = probar(contrato, columnas, filas, conteo_fuente, extra.get("conteo_de"))
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
    if fuente["tipo"] == "socrata":
        cita = (f"{fuente['titulo']}, {fuente['dominio'].replace('www.', '')} ({fuente['conjunto']}), "
                f"{fuente.get('filtro_legible') or fuente['filtro']}, consultado el {ahora:%d-%m-%Y}. {miles(len(filas))} {unidad}.")
    else:
        cita = f"{fuente['titulo']}, archivo {Path(fuente['ruta']).name}, leído el {ahora:%d-%m-%Y}. {miles(len(filas))} {unidad}."
    proc = {
        "tabla": tabla, "archivo": portable(destino), "fuente": fuente, "origen": origen, "llave": llave,
        "consulta": extra.get("consulta"), "paginas": extra.get("paginas"), "version_fuente": extra.get("version_fuente"),
        "columnas": contrato["columnas"], "consultado": ahora.isoformat(timespec="seconds"),
        "consultado_legible": f"{ahora:%d-%m-%Y %H:%M} (UTC{ahora:%z})", "filas": len(filas), "conteo_fuente": conteo_fuente,
        "sha256": huella, "sha256_anterior": anterior, "sin_cambios": anterior == huella,
        "nulos": nulos, "avisos": avisos, "nota": nota, "pruebas": pruebas, "cita": cita,
        "licencia": fuente.get("licencia"), "atribucion": fuente.get("atribucion"),
        "columnas_personales_justificadas": justificadas, "base_legal_sensibles": contrato.get("base_legal_sensibles", {}),
    }
    proc["estado"] = "aprobada" if aprobada else "rechazada"
    if not aprobada:
        proc["archivo"] = None
        proc["retirado"] = retirar(salida, tabla, "la carga no pasó sus pruebas", escribir=False)
    # una procedencia por tabla: con varias tablas, ninguna reemplaza a otra (ya no se escribe procedencia.json)
    (salida / f"procedencia_{tabla}.json").write_text(json.dumps(proc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ingesta {proc['estado']}: {miles(len(filas))} {unidad}" + (f" → {destino}" if aprobada else
                                                                         " (no se escribe el CSV: no pasó sus pruebas)"))
    for p in pruebas:
        print(f"  {'✓' if p['ok'] else '✗'} {p['prueba']}: {p['detalle']}")
    for a in avisos:
        print(f"  · aviso: {a}")
    if nota:
        print(f"  · nota: {nota}")
    print(f"  · nulos: {nulos}")
    print(f"  · {'sin cambios frente a la carga anterior' if proc['sin_cambios'] else 'archivo escrito' if aprobada else 'sin escribir'}"
          f" · sha256 {huella}")
    print(f"  · cita: {cita}")
    print("RESUMEN " + json.dumps({"estado": proc["estado"], "filas": len(filas), "conteo_fuente": conteo_fuente,
                                   "fallas": [p["prueba"] for p in pruebas if not p["ok"]]}, ensure_ascii=False))
    return 0 if proc["estado"] == "aprobada" else 1


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
    from contextlib import redirect_stdout
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
        with redirect_stdout(io.StringIO()):
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
    from contextlib import redirect_stdout
    sys.path.insert(0, str(Path(__file__).resolve().parent))
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
            with redirect_stdout(io.StringIO()):
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


def autoprueba():
    yo = sys.modules[__name__]
    fallas = comprobar_procedencia(yo)
    print("✓ procedencia: la consulta guardada reproduce la carga, con su versión y su hora con zona" if not fallas else "")
    otras = comprobar_varias_tablas(yo)
    print("✓ varias tablas: una procedencia por tabla, la rechazada no deja CSV y la huella del crudo se comprueba" if not otras else "")
    for f in fallas + otras:
        print(f"✗ {f}")
    print("RESUMEN " + json.dumps({"fallas": fallas + otras}, ensure_ascii=False))
    return 1 if fallas or otras else 0


def main(argv):
    if "--autoprueba" in argv:
        return autoprueba()
    if len(argv) < 3 or "--salida" not in argv:
        raise SystemExit(__doc__)
    salida = argv[argv.index("--salida") + 1]
    return ingerir(argv[0], salida, repetir="--repetir" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
