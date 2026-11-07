#!/usr/bin/env python3
"""Gobernanza determinista (sin IA): datos personales, salidas limpias y k-anonimato.

Uso:
  python gobernanza.py <corrida>        barre los datos de spec.json y las salidas de la corrida; escribe gobernanza.json
  python gobernanza.py --columnas a.csv muestra cómo se clasifica cada columna por su nombre

Qué hace:
  1. Clasifica cada columna por su nombre (y por su descripción en los metadatos, si la hay): identificador personal,
     cuasi-identificador, texto libre o sin marca. Los datos sensibles (Ley 1581, art. 5) cuentan como cuasi y la
     ingesta además les pide base legal. Una clave publicada que identifica a personas es un problema, con o sin k.
  2. Barre el texto libre con expresiones regulares (cédulas con contexto, correos, celulares,
     nombres con tratamiento) y entrega SOLO conteos y ejemplos enmascarados, nunca valores.
  3. Barre las salidas que se van a publicar (informe, resultado, gráfico, whitepaper y presentación, también en su
     versión impresa): deben salir en cero, y ninguna trae un texto con forma de instrucción para una IA.
  4. Calcula el k-anonimato del resultado si publica columnas de personas.
  5. Compara la clasificación de la IA (custodio.json) con la del barrido: lo que la IA no vio.
"""
import csv
import html
import json
import re
import sys
from pathlib import Path

ROLES = r"(representante|ordenador|supervisor|persona|contacto|funcionario|proveedor|contratista|beneficiario|titular|usuario|paciente|afiliado|ciudadano)"
PERSONAL = re.compile(
    rf"(nombre_{ROLES}|nombre_del_{ROLES}|nombre_completo|^nombres?$|^apellidos?$|nombres?_y_apellidos|representante_legal|"
    r"contratista|raz[oó_]n_social|"
    r"identificaci|identidad|c[ée]dula|^documento(?!s_tipo)|documento_(proveedor|persona|representante|identidad|de_identidad)|"
    r"doc_identidad|n_mero_de_documento|n[uú]mero_de_documento|numero_documento|num_documento|"
    r"proveedor_adjudicado|codigo_proveedor|nit_proveedor|^nit$|nit_(contratista|persona|beneficiario|titular)|"
    r"correo|e_?mail|(^|_)mail($|_)|tel[ée]fono|celular|(^|_)m[oó]vil($|_)|whatsapp|direcci|domicilio|"
    r"cuenta|banco|tarjeta|placa)", re.I)
CUASI = re.compile(r"(g[ée_]nero|sexo|edad|nacimiento|nacionalidad|estrato|tipodocproveedor|tipo_de_documento_|"
                   r"latitud|longitud|coordenada)", re.I)
# Datos sensibles (Ley 1581 de 2012, art. 5; los de niños, niñas y adolescentes, art. 7): cuentan como cuasi para todo
# lo demás y, además, la ingesta los rechaza si el contrato no registra la base legal (base_legal_sensibles).
SENSIBLE = re.compile(r"(etni|[ée]tnic|(^|_)raza($|_)|racial|ind[ií]gena|afrocolombian|afrodescendient|discapacidad|"
                      r"(^|_)salud|enfermedad|diagn[oó]stic|(^|_)vih($|_)|orientaci[oó]n_sexual|vida_sexual|sexualidad|"
                      r"biom[ée]tric|huella_dactilar|religi|creencia|afiliaci[oó]n_pol|partido_pol|sindica|"
                      r"menor(es)?_de_edad|^es_menor)", re.I)
TEXTO_LIBRE = re.compile(r"(objeto|descripcion_del_proceso|observaci|comentari|^detalle|_detalle|^notas?$|_notas?$|mensaje)", re.I)
# La descripción de la columna en los metadatos (Socrata: /api/views/<id>.json) delata lo que el nombre esconde
PERSONAL_DESC = re.compile(rf"(c[ée]dula|documento de identidad|n[uú]mero de (identificaci[oó]n|documento)|nombres? y apellidos|"
                           rf"nombre completo|apellidos|nombre del {ROLES}|correo electr[oó]nico|tel[ée]fono|celular|"
                           rf"direcci[oó]n de (residencia|domicilio|notificaci[oó]n)|domicilio|n[uú]mero de cuenta)", re.I)
CUASI_DESC = re.compile(r"(fecha de nacimiento|\bg[ée]nero\b|\bsexo\b|\bedad\b|nacionalidad|\bestrato\b|tipo de (documento|identificaci[oó]n))", re.I)
SENSIBLE_DESC = re.compile(r"(\betnia|[ée]tnic|\braza\b|racial|discapacidad|orientaci[oó]n sexual|vida sexual|biom[ée]tric|"
                           r"huella dactilar|religi[oó]n|afiliaci[oó]n pol[ií]tica|partido pol[ií]tico|sindica|menor(es)? de edad)", re.I)
PATRONES = {
    "cédula con contexto": re.compile(
        # cada parte opcional consume sus propios espacios: con tres «\s*» seguidos, una nota con miles de espacios
        # tardaba decenas de segundos (retroceso cúbico, hallado por la revisión ciega del verificador de la presentación)
        r"\b(?:c\.\s?c\.?|cc|c[ée]dula(?:\s+de\s+ciudadan[ií]a)?|identificad[oa]\s+con)(?:\s*(?:no\.?|n[°º.]|n[úu]mero))?(?:\s*[:#])?\s*"
        r"(\d{1,3}(?:[.\s]?\d{3}){1,3})\b", re.I),
    "correo": re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
    # con contexto (cel., teléfono…) o con separadores; un número suelto de 10 dígitos puede ser un valor en pesos
    "celular": re.compile(
        r"(?i:(?:cel(?:ular)?|tel(?:[ée]fono)?|m[óo]vil|whatsapp|contacto)\.?(?:\s*:)?\s*(?:\+?57\s?)?3\d{2}[\s-]?\d{3}[\s-]?\d{4})"
        r"|\+57\s?3\d{9}(?!\d)|(?<![\d.,])3\d{2}[\s-]\d{3}[\s-]?\d{4}(?![\d.,])"),
    "nombre con tratamiento": re.compile(
        r"\b(?i:señor|señora|sr\.|sra\.|don|doña)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}"),
}
K_MINIMO = 5
INSTRUCCION = re.compile(
    r"(ignor[ae]\w*\s+(las\s+|todas\s+las\s+|tus\s+)?(instrucciones|reglas|indicaciones)|ignore\s+(all\s+|the\s+|any\s+)?(previous|prior|above)?\s*instructions"
    r"|olvida\w*\s+(las|tus|todas)|forget\s+(all|your|previous)|you\s+are\s+now|ahora\s+eres|act[uú]a\s+como|\bact\s+as\b"
    r"|nota\s+para\s+(la\s+)?(ia|ai|el\s+agente|el\s+asistente|el\s+modelo)|instrucci[oó]n\s+para\s+(la\s+ia|el\s+(agente|graficador|especificador|generador|revisor))"
    r"|(system|sistema)\s*prompt|instrucciones\s+del\s+sistema|<\|im_start\|>|\[/?INST\]"
    r"|apru[eé]ba\w*\s+(este|el|la|esta)\s+(aporte|corrida|cambio|pull)|approve\s+this|merge\s+this|aprobad[oa]\s+por\s+auditor"
    r"|(salta|saltar|desactiva|desactivar|omite|omitir|disable|bypass|skip)\s+(la\s+|el\s+|the\s+)?(compuerta|filtro|verificaci[oó]n|gate|filter|check)"
    r"|sin\s+correr\s+el\s+filtro|ya\s+no\s+aplica"
    r"|(debe|deben|tiene\s+que|tienen\s+que)\s+(leer|abrir|consultar|copiar)\s+(el\s+|la\s+|los\s+)?(reglas\.py|caso_conocido|esperado\.json|sellos))", re.I)
COMENTARIO_OCULTO = re.compile(r"<!--(.*?)-->", re.S)


def parece_instruccion(texto):
    """Texto que da órdenes a una IA, escondido en los datos o en un aporte (inyección de instrucciones)."""
    t = str(texto or "")
    if INSTRUCCION.search(t):
        return True
    return any(re.search(r"\b(agente|ia|ai|assistant|asistente|claude|gpt|modelo|llm|aprueba|approve|merge)\b", c, re.I)
               for c in COMENTARIO_OCULTO.findall(t))


def clasificar_columna(nombre, descripcion=None):
    """personal: identifica a una persona; cuasi: combinada puede identificarla (los datos sensibles también son
    cuasi, ver es_sensible); texto_libre: puede traer nombres o cédulas escritos a mano (en SECOP, cerca de 1 de cada
    1.000 filas). Todas piden justificación en la ingesta. Con la descripción de los metadatos, si el nombre no dice
    nada, decide la descripción («campo_7: Número de cédula del beneficiario» es personal)."""
    if PERSONAL.search(nombre):
        return "personal"
    if es_sensible(nombre, descripcion) or CUASI.search(nombre):
        return "cuasi"
    if TEXTO_LIBRE.search(nombre):
        return "texto_libre"
    if descripcion and PERSONAL_DESC.search(descripcion):
        return "personal"
    if descripcion and CUASI_DESC.search(descripcion):
        return "cuasi"
    return None


def es_sensible(nombre, descripcion=None):
    """Dato sensible (Ley 1581 de 2012, art. 5: origen racial o étnico, salud, vida sexual, biométricos, convicciones,
    afiliación sindical o política; art. 7: menores de edad). La ingesta lo rechaza sin base legal registrada."""
    return bool(SENSIBLE.search(nombre) or (descripcion and SENSIBLE_DESC.search(descripcion)))


def enmascarar(texto):
    t = re.sub(r"\d", "•", texto)
    return t[:3] + "•" * max(0, min(len(t) - 3, 8)) if len(t) > 3 else "•••"


def escanear_texto(texto):
    out = {}
    for nombre, rx in PATRONES.items():
        hallados = rx.findall(texto) if texto else []
        if hallados:
            out[nombre] = len(hallados)
    return out


def leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        lector = csv.DictReader(fh, strict=True)
        return lector.fieldnames or [], list(lector)


def barrer_tabla(ruta):
    cols, filas = leer_csv(ruta)
    res = {"ruta": str(ruta), "filas": len(filas), "columnas": {}}
    for c in cols:
        clase = clasificar_columna(c)
        valores = [f.get(c) or "" for f in filas]
        largo = sum(len(v) for v in valores) / max(1, len(valores))
        info = {"clase_por_nombre": clase, "texto_libre": largo > 40}
        if not clase and not any(v and not v.replace(".", "").replace("-", "").isdigit() for v in valores[:500]):
            res["columnas"][c] = info
            continue
        conteo, filas_con = {}, 0
        ejemplos = []
        for v in valores:
            h = escanear_texto(v)
            if h:
                filas_con += 1
                for k, n in h.items():
                    conteo[k] = conteo.get(k, 0) + n
                if len(ejemplos) < 3:
                    for nombre, rx in PATRONES.items():
                        m = rx.search(v)
                        if m:
                            ejemplos.append(f"{nombre}: {enmascarar(m.group(0))}")
                            break
        if conteo:
            info.update({"hallazgos": conteo, "filas_con_hallazgos": filas_con,
                         "por_cada_mil_filas": round(1000 * filas_con / max(1, len(filas)), 2),
                         "ejemplos_enmascarados": ejemplos})
        res["columnas"][c] = info
    return res


# Lo que se publica de una corrida. El whitepaper y la presentación ya los revisan W5 (validar_whitepaper.py) y
# verificar_presentacion.py; aquí se barren igual, con las mismas reglas que el resto, para que gobernanza.json diga
# de todas las salidas y no dependa de que esos dos se hayan corrido (L87).
SALIDAS = ("informe.md", "informe_final.md", "informe_final.html", "grafico.html", "presentacion.html", "informe.json",
           "hipotesis_resultado.json", "whitepaper.md", "WHITEPAPER.html", "presentacion.json")
CON_INSTRUCCIONES = ("informe.md", "informe_final.md", "whitepaper.md", "WHITEPAPER.html", "presentacion.json",
                     "presentacion.html")


def texto_publicado(p):
    """El texto que se publica de una salida: las cadenas de un JSON (no los números: un valor en pesos no es un dato
    personal; de informe.json, solo el resultado oficial); de un HTML, sin el paquete de Plotly y con las entidades
    resueltas (un «&#64;» no esconde un correo)."""
    texto = p.read_text(encoding="utf-8", errors="ignore")
    if p.suffix == ".json":
        def cadenas(x):
            if isinstance(x, dict):
                return " ".join(cadenas(v) for v in x.values())
            if isinstance(x, list):
                return " ".join(cadenas(v) for v in x)
            return x if isinstance(x, str) else ""
        try:
            datos = json.loads(texto)
            texto = cadenas(datos.get("resultado_oficial") if p.name == "informe.json" else datos)
        except Exception:
            pass
    if p.name == "grafico.html":
        texto = re.sub(r"<script[^>]*plotly[^>]*>.*?</script>", " ", texto, flags=re.S)[:2_000_000]
    if p.suffix == ".html":
        texto = html.unescape(texto)
    return texto


def barrer_salidas(c):
    archivos = [c / n for n in SALIDAS if (c / n).exists()]
    out = {}
    for p in archivos:
        out[p.name] = escanear_texto(texto_publicado(p))
    return out


def k_anonimato(resultado, claves):
    personales = [k for k in claves if clasificar_columna(k) in ("personal", "cuasi")]
    if not personales:
        return {"aplica": False, "motivo": "el resultado no publica columnas de personas (son agregados)"}
    grupos = {}
    for f in resultado:
        g = tuple(str(f.get(k)) for k in personales)
        grupos[g] = grupos.get(g, 0) + 1
    k = min(grupos.values()) if grupos else 0
    return {"aplica": True, "columnas": personales, "k": k, "k_minimo": K_MINIMO, "ok": k >= K_MINIMO}


def comparar_custodio(c, tablas):
    """La IA clasifica TODAS las columnas de la fuente (con metadatos, sin filas); el código clasifica las mismas
    por su nombre y barre el texto de las que se ingirieron. Se reporta en qué no coinciden."""
    ruta = c / "custodio.json"
    if not ruta.exists():
        return {"hay_custodio": False}
    ia = json.loads(ruta.read_text(encoding="utf-8"))
    clase_ia = {x["columna"]: x.get("clase") for x in ia.get("columnas", [])}
    marcadas_ia = {k for k, v in clase_ia.items() if v in ("personal", "cuasi")}
    marcadas_codigo = {k for k in clase_ia if clasificar_columna(k)}
    for t in tablas.values():
        for col, info in t["columnas"].items():
            if info.get("clase_por_nombre") or info.get("hallazgos"):
                marcadas_codigo.add(col)
    ingeridas = {col for t in tablas.values() for col in t["columnas"]}
    return {"hay_custodio": True, "columnas_fuente": len(clase_ia), "ia_no_vio": sorted(marcadas_codigo - marcadas_ia),
            "solo_la_ia": sorted(marcadas_ia - marcadas_codigo), "coinciden": sorted(marcadas_ia & marcadas_codigo),
            "personales_que_la_ingesta_dejo_fuera": sorted((marcadas_ia | marcadas_codigo) - ingeridas)}


def gobernar(c):
    from rutas import resolver_datos
    spec = resolver_datos(json.loads((c / "spec.json").read_text(encoding="utf-8")))
    tablas = {t: barrer_tabla(r) for t, r in spec["datos"].items()}
    salidas = barrer_salidas(c)
    inf = json.loads((c / "informe.json").read_text(encoding="utf-8")) if (c / "informe.json").exists() else {}
    k = k_anonimato(inf.get("resultado_oficial") or [], spec["salida"]["claves"])
    custodio = comparar_custodio(c, tablas)
    problemas = [f"{n}: {h}" for n, h in salidas.items() if h]
    for p in [c / n for n in CON_INSTRUCCIONES]:
        if p.exists() and parece_instruccion(re.sub(r"(?s)<!--.*?-->", "", texto_publicado(p))):
            problemas.append(f"{p.name}: trae un texto con forma de instrucción para una IA (posible inyección en los datos)")
    if k.get("aplica") and not k.get("ok"):
        problemas.append(f"k-anonimato {k['k']} < {K_MINIMO} en {k['columnas']}")
    # una clave que identifica (nombre, documento, NIT de persona, contacto) o un dato sensible no se publica ni con k alto
    identifican = [x for x in spec["salida"]["claves"] if clasificar_columna(x) == "personal" or es_sensible(x)]
    if identifican:
        problemas.append(f"el resultado publica columnas que identifican a personas o son datos sensibles: {identifican}")
    if custodio.get("ia_no_vio"):
        problemas.append(f"la IA no marcó como personales: {custodio['ia_no_vio']} (el barrido sí)")
    usadas = set(spec.get("columnas_usadas") or [])
    personales_usadas = sorted(col for t in tablas.values() for col, i in t["columnas"].items()
                               if col in usadas and i.get("clase_por_nombre") == "personal")
    if personales_usadas:
        problemas.append(f"el análisis usa columnas personales: {personales_usadas}")
    out = {"tablas": tablas, "salidas": salidas, "k_anonimato": k, "custodio": custodio,
           "personales_usadas": personales_usadas, "claves_que_identifican": identifican, "problemas": problemas,
           "estado": "aprobado" if not problemas else "revisar"}
    (c / "gobernanza.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gobernanza: {out['estado']}")
    for p in problemas:
        print(f"  - {p}")
    for t, info in tablas.items():
        for col, i in info["columnas"].items():
            if i.get("clase_por_nombre") or i.get("hallazgos"):
                print(f"  · {t}.{col}: {i.get('clase_por_nombre') or ''} {i.get('hallazgos') or ''} "
                      f"{i.get('ejemplos_enmascarados') or ''}".rstrip())
    print("RESUMEN " + json.dumps({"estado": out["estado"], "problemas": problemas}, ensure_ascii=False))
    return 0 if not problemas else 1


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    if argv[0] == "--columnas":
        cols, _ = leer_csv(argv[1])
        for col in cols:
            print(f"{col}: {clasificar_columna(col) or '—'}")
        return 0
    return gobernar(Path(argv[0]).resolve())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
