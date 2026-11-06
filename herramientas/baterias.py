#!/usr/bin/env python3
"""Baterías: lo que falló una vez se vuelve prueba para siempre (sin IA).

Uso:
  python baterias.py                         corre todas las baterías
  python baterias.py --agregar-malo nombre archivo.py   guarda un hallazgo confirmado como código que debe bloquearse
  python baterias.py --leccion "texto" --origen "..." --prueba "..."   agrega una lección

1. Seguridad: todo lo de baterias/seguridad/malos debe quedar bloqueado y todo lo de buenos debe pasar
   (así también se prueba al probador: un falso positivo es una falla de la compuerta). Lo mismo con el perfil de
   usuario: malos_usuario se bloquea; buenos_usuario y buenos pasan.
2. Privacidad: el perfil de un CSV con datos personales no puede mostrar ninguno de los valores de
   no_deben_salir.txt, y el barrido de gobernanza tiene que encontrarlos.
3. Lecciones: cada lección apunta a una prueba; si apunta a un archivo de la batería, el archivo existe.
4. Cruces: el perfil explica por qué no cruza cada valor (baterias/cruces/esperado.json) y no explica un ausente.
5. Fechas: el perfil cuenta aparte las fechas que no existen en el calendario (baterias/fechas/casos.json).
6. Repetidos: una llave repetida nunca se resuelve por el orden del archivo sin aviso (baterias/limpieza/).
7. Factor: el perfil reconoce el factor de expansión de una encuesta (baterias/perfil/).
8. Gráfico: las figuras de baterias/grafico/buenos pasan las comprobaciones de forma y color, y cada figura de
   malos falla justo la comprobación que ataca (ni otra, ni ninguna).
"""
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
BAT = RAIZ / "baterias"
sys.path.insert(0, str(AQUI))
import dependencias  # noqa: E402
import seguridad  # noqa: E402
from gobernanza import barrer_tabla  # noqa: E402


def falla(caso, texto):
    """Una falla con el caso que la produce: así el filtro de aportes distingue el hueco que encontró un caso nuevo."""
    return {"caso": str(caso), "falla": texto}


def bloquea(ruta):
    d = dependencias.revisar(ruta)
    s, _ = seguridad.revisar([ruta])
    return bool(d.get("no_permitidas") or d.get("intenta_instalar") or s[0]["bloquean"])


def bateria_seguridad():
    fallas = []
    malos = sorted((BAT / "seguridad" / "malos").glob("*.py"))
    buenos = sorted((BAT / "seguridad" / "buenos").glob("*.py"))
    for p in malos:
        if not bloquea(p):
            fallas.append(falla(p.name, f"no se bloqueó {p.name}"))
    for p in buenos:
        if bloquea(p):
            fallas.append(falla(p.name, f"falso positivo: se bloqueó {p.name}"))
    # Perfil de usuario: el código que sí usa red y archivos. Lo bueno del pipeline también tiene que pasar aquí.
    malos_u = sorted((BAT / "seguridad" / "malos_usuario").glob("*.py"))
    buenos_u = sorted((BAT / "seguridad" / "buenos_usuario").glob("*.py"))
    if malos_u or buenos_u:
        res, _ = seguridad.revisar(malos_u + buenos_u + buenos, "usuario")
        for r in res:
            nombre, bloqueado = Path(r["archivo"]), bool(r["bloquean"])
            if nombre.parent.name == "malos_usuario" and not bloqueado:
                fallas.append(falla(nombre.name, f"perfil usuario: no se bloqueó {nombre.name}"))
            elif nombre.parent.name != "malos_usuario" and bloqueado:
                fallas.append(falla(nombre.name, f"perfil usuario: falso positivo en {nombre.name}: {r['bloquean'][0]['regla']}"))
    return {"bateria": "seguridad", "casos": len(malos) + len(buenos) + len(malos_u) + len(buenos_u), "fallas": fallas}


def bateria_privacidad():
    fallas = []
    csv_ = BAT / "privacidad" / "con_datos_personales.csv"
    secretos = [s for s in (BAT / "privacidad" / "no_deben_salir.txt").read_text(encoding="utf-8").splitlines() if s]
    p = subprocess.run([sys.executable, str(AQUI / "perfilar.py"), f"t={csv_}"], capture_output=True, text=True)  # nosec B603
    for s in secretos:
        if s in p.stdout:
            fallas.append(falla(s, f"el perfil muestra un dato personal: {s[:3]}…"))
    from gobernanza import escanear_texto
    for t in (BAT / "privacidad" / "no_son_personales.txt").read_text(encoding="utf-8").splitlines():
        if t and escanear_texto(t):
            fallas.append(falla(t, f"falso positivo: «{t}» se marcó como dato personal {escanear_texto(t)}"))
    barrido = barrer_tabla(csv_)
    detectadas = {c for c, i in barrido["columnas"].items() if i.get("hallazgos") or i.get("clase_por_nombre") == "personal"}
    for c in ("proveedor_adjudicado", "documento_proveedor", "objeto_del_contrato"):
        if c not in detectadas:
            fallas.append(falla(c, f"el barrido no detectó {c}"))
    from gobernanza import clasificar_columna
    cols = json.loads((BAT / "privacidad" / "columnas_secop.json").read_text(encoding="utf-8"))
    n_cols = 0
    for grupo, aceptadas in (("personal", {"personal"}), ("cuasi_o_personal", {"personal", "cuasi"}),
                             ("texto_libre", {"texto_libre"}), ("sin_marca", {None})):
        for c in cols[grupo]:
            n_cols += 1
            if clasificar_columna(c) not in aceptadas:
                fallas.append(falla(c, f"columna de SECOP mal clasificada: {c} → {clasificar_columna(c)} (se esperaba {grupo})"))
    return {"bateria": "privacidad", "casos": len(secretos) + 3 + 6 + n_cols, "fallas": fallas}


def ingerir_local(p, carpeta):
    """La ingesta local de un CSV con un contrato mínimo (todas las columnas como texto y justificadas: son casos
    ficticios). Devuelve su RESUMEN."""
    with open(p, newline="", encoding="utf-8-sig") as fh:
        cab = next(csv.reader(fh), None) or ["vacio"]
    contrato = {"fuente": {"tipo": "local", "ruta": str(p), "titulo": "caso de la batería", "licencia": "—",
                           "atribucion": "—", "unidad": "filas"},
                "tabla": "caso", "llave": cab[0], "columnas": {c: "texto" for c in cab},
                "personales_justificadas": {c: "caso de prueba con valores ficticios" for c in cab}}
    (carpeta / "contrato.json").write_text(json.dumps(contrato, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(AQUI / "ingesta.py"), str(carpeta / "contrato.json"), "--salida",  # nosec B603
                        str(carpeta / "salida")], capture_output=True, text=True)
    linea = next((l for l in reversed(r.stdout.splitlines()) if l.startswith("RESUMEN ")), None)
    return json.loads(linea[len("RESUMEN "):]) if linea else {"estado": "sin RESUMEN", "salida": r.stderr[-160:]}


def bateria_failfast():
    """Un CSV mal formado detiene la lectura: nunca se lee a medias ni se rellena en silencio (FAILFAST). Se prueba con
    los dos lectores de las reglas (leer_csv y recorrer_csv, que recorre fila por fila con las mismas detenciones) y
    con la ingesta local, que es la que escribe los datos del pipeline: la ingesta debe rechazarlo y decir en qué
    línea. Control positivo: los CSV bien formados de ejemplo/datos se leen completos, con los dos lectores y con la
    ingesta."""
    from reglas_base import contar_registros, leer_csv, recorrer_csv
    fallas, casos = [], sorted((BAT / "failfast").glob("*.csv"))
    lectores = (("leer_csv", leer_csv), ("recorrer_csv", lambda p: sum(1 for _ in recorrer_csv(p))))   # los dos, igual
    buenos = sorted((BAT / "failfast" / "se_leen").glob("*.csv"))   # y lo legítimo de cualquier fuente se lee (sin falsas alarmas)
    controles = sorted((RAIZ / "ejemplo" / "datos").glob("*.csv"))
    tmp = Path(tempfile.mkdtemp(prefix="bateria-failfast-"))
    try:
        for p in casos:
            for nombre, leer in lectores:
                try:
                    leer(p)
                    fallas.append(falla(p.name, f"{p.name} se leyó sin error con {nombre}"))
                except Exception:
                    pass
            r = ingerir_local(p, tmp)
            if r.get("estado") != "rechazada" or not re.search(r"l[ií]nea \d+", str(r.get("motivo") or "")):
                fallas.append(falla(p.name, f"la ingesta local no rechazó {p.name} diciendo la línea: {str(r)[:160]}"))
        for p in buenos:
            for nombre, leer in lectores:
                try:
                    leer(p)
                except Exception as e:
                    fallas.append(falla(p.name, f"falsa alarma con {nombre}: {p.name} se detuvo ({str(e)[:80]})"))
        for p in controles:
            esperado = contar_registros(p.read_text(encoding="utf-8-sig"))
            for nombre, contar in (("leer_csv", lambda x: len(leer_csv(x))), ("recorrer_csv", lambda x: sum(1 for _ in recorrer_csv(x)))):
                try:
                    n = contar(p)
                except Exception as e:
                    n = f"se detuvo ({str(e)[:80]})"
                if n != esperado:
                    fallas.append(falla(p.name, f"control positivo: {p.name} bien formado no se leyó completo con {nombre} ({esperado} filas): {n}"))
            r = ingerir_local(p, tmp)
            de_formato = {"conteo contra la fuente", "tipos declarados (FAILFAST)"} & set(r.get("fallas") or [])
            if r.get("motivo") or de_formato or r.get("filas") != esperado or r.get("conteo_fuente") != esperado:
                fallas.append(falla(p.name, f"control positivo: {p.name} bien formado no se leyó completo ({esperado} filas): {str(r)[:160]}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {"bateria": "failfast", "casos": 3 * len(casos) + 2 * len(buenos) + 3 * len(controles), "fallas": fallas}


def bateria_inyeccion():
    """Instrucciones disfrazadas: los textos maliciosos deben detectarse y los legítimos no (sin falsas alarmas)."""
    from gobernanza import parece_instruccion
    malos = [l for l in (BAT / "inyeccion" / "maliciosos.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    buenos = [l for l in (BAT / "inyeccion" / "legitimos.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    fallas = [falla(m, f"no detecta: «{m[:60]}»") for m in malos if not parece_instruccion(m)]
    fallas += [falla(b, f"falsa alarma: «{b[:60]}»") for b in buenos if parece_instruccion(b)]
    return {"bateria": "inyeccion", "casos": len(malos) + len(buenos), "fallas": fallas}


def bateria_cruces():
    """Por qué no cruza un valor entre tablas: espacios internos o invisibles; tildes, puntuación o ceros a la izquierda."""
    from perfilar import perfilar
    d = BAT / "cruces"
    esperado = json.loads((d / "esperado.json").read_text(encoding="utf-8"))
    p = perfilar({"origen": str(d / "origen.csv"), "destino": str(d / "destino.csv")})
    fallas, casos = [], 0
    for col, claves in esperado.items():
        if col.startswith("_"):
            continue
        x = next((c for c in p["cruces"] if c["desde"] == "origen" and c["columna"] == col), None)
        if x is None:
            fallas.append(falla(col, f"{col}: el perfil no reporta el cruce"))
            continue
        obtenido = {**x, **x.get("de_los_que_no_cruzan", {})}
        for k, v in claves.items():
            casos += 1
            if obtenido.get(k) != v:
                fallas.append(falla(col, f"{col}.{k}: {obtenido.get(k)} (se esperaba {v})"))
    return {"bateria": "cruces", "casos": casos, "fallas": fallas}


def bateria_fechas():
    """Una fecha que no existe en el calendario (mes 13, 30 de febrero) se cuenta aparte y no entra al rango."""
    from perfilar import perfil_fechas
    d = json.loads((BAT / "fechas" / "casos.json").read_text(encoding="utf-8"))
    fallas = []
    for c in d["casos"]:
        p = perfil_fechas(c["valores"]) or {}
        obtenido = {**p, "fechas_imposibles": p.get("fechas_imposibles", 0)}
        for k, v in c.items():
            if k not in ("nombre", "valores") and obtenido.get(k) != v:
                fallas.append(falla(c['nombre'], f"{c['nombre']}: {k} = {obtenido.get(k)} (se esperaba {v})"))
    return {"bateria": "fechas", "casos": len(d["casos"]), "fallas": fallas}


def bateria_repetidos():
    """Llaves repetidas: nunca gana una fila por el orden del archivo sin avisarlo; el desempate del plan decide."""
    import csv
    import tempfile
    import limpieza
    d = BAT / "limpieza"
    esperado = json.loads((d / "repetidos_esperado.json").read_text(encoding="utf-8"))
    fallas = []
    for c in esperado["casos"]:
        tmp = Path(tempfile.mkdtemp(prefix="bateria-repetidos-"))
        try:
            op = {"op": "repetidos", "columnas": ["id"], "marca": "repetido"}
            if c["desempate"]:
                op["desempate"] = c["desempate"]
            plan = {"tabla": "t", "entrada": str(d / "repetidos.csv"), "salida": str(tmp / "t.csv"), "llave": "id", "operaciones": [op]}
            (tmp / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            inf = limpieza.limpiar(tmp / "plan.json", informe=False)
            ok = {f["id"]: f["region"] for f in csv.DictReader(open(tmp / "t.csv", encoding="utf-8")) if f.get("calidad_ok") == "1"}
            for k, v in c["conserva"].items():
                if ok.get(k) != v:
                    fallas.append(falla(c['nombre'], f"{c['nombre']}: {k} conserva {ok.get(k)} (se esperaba {v})"))
            aviso = inf["operaciones"][0].get("aviso")
            if (c["aviso"] is None) != (aviso is None) or (c["aviso"] and c["aviso"] not in aviso):
                fallas.append(falla(c['nombre'], f"{c['nombre']}: aviso «{aviso}» (se esperaba «{c['aviso']}»)"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return {"bateria": "repetidos", "casos": len(esperado["casos"]), "fallas": fallas}


def bateria_factor():
    """Encuestas: el perfil reconoce el factor de expansión (cifras de población ponderadas, no conteo de filas)."""
    from perfilar import perfil_columna
    d = json.loads((BAT / "perfil" / "factor_de_expansion.json").read_text(encoding="utf-8"))
    fallas = []
    for c in d["casos"]:
        es = "factor_de_expansion" in perfil_columna(c["columna"], c["valores"])
        if es != c["es_factor"]:
            fallas.append(falla(c["columna"], f"{c['columna']} {c['valores'][:2]}: {'marcado' if es else 'no marcado'} como factor de expansión"))
    return {"bateria": "factor", "casos": len(d["casos"]), "fallas": fallas}


def bateria_grafico():
    """Forma y color del gráfico, sobre el JSON de la figura (sin caja de arena): los buenos pasan todo y cada malo
    falla solo la comprobación que ataca. Un falso positivo también es una falla (L32)."""
    from verificar_grafico import comprobar_forma_y_color
    fallas, nombres, atacadas = [], set(), set()
    buenos = sorted((BAT / "grafico" / "buenos").glob("*.json"))
    malos = sorted((BAT / "grafico" / "malos").glob("*.json"))
    for p in buenos:
        res = comprobar_forma_y_color(json.loads(p.read_text(encoding="utf-8"))["figura"])
        nombres |= {c["comprobacion"] for c in res}
        fallan = [c["comprobacion"] for c in res if not c["ok"]]
        if fallan:
            fallas.append(falla(p.name, f"falso positivo en {p.name}: {fallan}"))
    for p in malos:
        caso = json.loads(p.read_text(encoding="utf-8"))
        res = comprobar_forma_y_color(caso["figura"])
        nombres |= {c["comprobacion"] for c in res}
        fallan = [c["comprobacion"] for c in res if not c["ok"]]
        objetivo = caso.get("debe_fallar")
        atacadas.add(objetivo)
        if objetivo not in {c["comprobacion"] for c in res}:
            fallas.append(falla(p.name, f"{p.name}: no existe la comprobación «{objetivo}»"))
        elif fallan != [objetivo]:
            fallas.append(falla(p.name, f"{p.name}: falla {fallan or 'ninguna'}; se esperaba solo «{objetivo}»"))
    fallas += [falla(n, f"sin caso malo para «{n}»") for n in sorted(nombres - atacadas)]
    return {"bateria": "grafico", "casos": len(buenos) + len(malos), "fallas": fallas}


def bateria_lecciones():
    d = json.loads((BAT / "lecciones.json").read_text(encoding="utf-8"))
    fallas = []
    for l in d["lecciones"]:
        prueba = l.get("prueba", "")
        if not prueba:
            fallas.append(falla(l['id'], f"{l['id']} no tiene prueba"))
        for parte in prueba.split():
            if parte.startswith("bateria:"):
                ruta = parte.split(":", 1)[1]
                if not ((BAT / ruta).exists() or (RAIZ / ruta).exists()):
                    fallas.append(falla(l['id'], f"{l['id']}: no existe {parte}"))
    return {"bateria": "lecciones", "casos": len(d["lecciones"]), "fallas": fallas}


def main(argv):
    if "--agregar-malo" in argv:
        i = argv.index("--agregar-malo")
        nombre, origen = argv[i + 1], Path(argv[i + 2])
        destino = BAT / "seguridad" / "malos" / f"{nombre}.py"
        shutil.copy(origen, destino)
        print(f"Agregado {destino.name}. {'Se bloquea hoy.' if bloquea(destino) else 'HOY NO SE BLOQUEA: hay que mejorar la compuerta.'}")
        return 0
    if "--leccion" in argv:
        d = json.loads((BAT / "lecciones.json").read_text(encoding="utf-8"))
        g = lambda k: argv[argv.index(k) + 1] if k in argv else ""
        ident = g("--id") or f"L{len(d['lecciones']) + 1:02d}"   # en un aporte: --id L-<usuario>-<tema>; el dueño renumera al aceptar
        d["lecciones"].append({"id": ident, "leccion": g("--leccion"), "origen": g("--origen"), "prueba": g("--prueba")})
        (BAT / "lecciones.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Lección {d['lecciones'][-1]['id']} agregada.")
        return 0
    res = [correr_bateria(fn) for fn in (bateria_seguridad, bateria_privacidad, bateria_failfast, bateria_inyeccion,
                                         bateria_cruces, bateria_fechas, bateria_repetidos, bateria_factor,
                                         bateria_grafico, bateria_lecciones)]
    for r in res:
        print(f"{'✓' if not r['fallas'] else '✗'} {r['bateria']}: {r['casos']} casos"
              + ("" if not r["fallas"] else " · " + "; ".join(f["falla"] for f in r["fallas"])))
    malos = sum(len(r["fallas"]) for r in res)
    detalle = [{"bateria": r["bateria"], "caso": f["caso"], "falla": f["falla"][:300]} for r in res for f in r["fallas"]]
    print("RESUMEN " + json.dumps({"baterias": len(res), "fallas": malos, "errores": [r["bateria"] for r in res if r.get("error")],
                                   "detalle": detalle[:200]}, ensure_ascii=False))
    return 1 if malos else 0


def correr_bateria(fn):
    """Si una batería se cae, cuenta como falla y las demás siguen corriendo: nunca se pierde el resto en silencio."""
    try:
        r = fn()
        r["fallas"] = [f if isinstance(f, dict) else falla("", f) for f in r["fallas"]]
        return r
    except Exception as e:
        return {"bateria": fn.__name__.replace("bateria_", ""), "casos": 0, "error": True,
                "fallas": [falla("", f"ERROR: la batería no terminó: {type(e).__name__}: {str(e)[:160]}")]}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
