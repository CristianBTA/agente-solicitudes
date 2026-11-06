"""Base para escribir las reglas de una corrida (reglas.py).

Cada regla recibe `datos` ({tabla: ruta_csv}) y `resultado` (lista de filas) y devuelve
(ok, mensaje). Las reglas leen los CSV por su cuenta, así sirven igual para los datos
reales y para el caso con respuesta conocida.

    from reglas_base import regla, leer_csv, aprox

    @regla("R1", "conservacion", "El total del resultado es igual al total de la fuente")
    def r1(datos, resultado):
        ...
        return aprox(a, b), f"resultado {a:,.0f} · fuente {b:,.0f}"
"""
import csv
import io
import re

REGLAS = []


def regla(id, tipo, descripcion):
    def decorar(fn):
        REGLAS.append({"id": id, "tipo": tipo, "descripcion": descripcion, "fn": fn})
        return fn
    return decorar


_PUNTO_DE_MILES = re.compile(r"^[-+]?[1-9]\d{0,2}(\.\d{3})+(,\d+)?$")   # 78.000 · 1.250.000 · 1.250,50
_ENTERO_LARGO = re.compile(r"^[-+]?\d{4,}$")                            # 1628100
_NUMERICO = re.compile(r"^[-+]?\d[\d.]*(,\d+)?$")                  # solo cifras, puntos y una coma decimal
_PUNTO_DECIMAL = re.compile(r"\.(\d{1,2}|\d{4,})(?!\d)")         # 12.5 · 3.14159: en esa columna el punto es decimal


def _lector_estricto(fh, origen, formulas=True):
    """El encabezado y un generador de (línea, campos) con las detenciones de FAILFAST que comparten leer_tabla (y con
    ella leer_csv, la ingesta local y la limpieza) y recorrer_csv: archivo vacío, separador que no es la coma, columnas
    repetidas en el encabezado, una comilla sin cerrar, una línea vacía, una fila con más o menos campos que el
    encabezado o una celda con una fórmula de Excel como texto («=DAY(J2)»), todas con el número de la línea física.
    Con formulas=False la fórmula no detiene la lectura: la limpieza la neutraliza y la marca (DB5)."""
    lector = csv.reader(fh, strict=True)

    def siguiente():
        try:
            return next(lector)
        except StopIteration:
            return None
        except csv.Error as e:
            raise ValueError(f"la línea {lector.line_num} {origen} no se puede leer ({e}): ¿una comilla sin cerrar?") from None

    cab = siguiente()
    if not cab:
        raise ValueError(f"la línea 1 {origen} está vacía: no hay encabezado")
    if len(cab) == 1 and any(sep in cab[0] for sep in (";", "\t", "|")):
        raise ValueError(f"la línea 1 {origen} (el encabezado) tiene una sola columna con «;», tabulador o «|»: el separador no es la coma")
    repetidas = sorted({c for c in cab if cab.count(c) > 1})
    if repetidas:
        raise ValueError(f"la línea 1 {origen} (el encabezado) repite columnas: {repetidas}")

    def filas():
        while (f := siguiente()) is not None:
            n = lector.line_num
            if not f:
                raise ValueError(f"la línea {n} {origen} está vacía")
            if len(f) != len(cab):
                raise ValueError(f"la línea {n} {origen} no tiene el mismo número de campos que el encabezado ({len(f)} y {len(cab)})")
            if formulas and "=" in "\x1f".join(f):    # celda por celda solo donde hay un «=» (escala a millones de filas, L49)
                for col, v in zip(cab, f):
                    if v.lstrip().startswith("="):
                        raise ValueError(f"la línea {n} {origen}, columna «{col}», trae una fórmula de Excel como texto, no su valor: "
                                         "hay que exportar los valores (Pegado especial → Valores) antes de leer")
            yield n, f

    return cab, filas()


def leer_tabla(texto, origen="del CSV", miles=True, formulas=True, ver=None):
    """Encabezado, filas (listas de texto) y la línea física donde termina cada fila, sin convertir nada.
    FAILFAST: archivo vacío, separador que no es la coma, columnas repetidas en el encabezado, una comilla sin cerrar,
    una línea vacía, una fila con más o menos campos que el encabezado o una celda con una fórmula de Excel como texto
    («=DAY(J2)») detienen la lectura con el número de línea; nunca se lee a medias ni se rellena en silencio.
    miles=False y formulas=False dejan esas dos revisiones a quien llama (la limpieza: su operación numero declara el
    decimal y las fórmulas se neutralizan); ver(columna, valor) decide cómo sale un valor en el mensaje (la ingesta
    enmascara los de las columnas personales)."""
    cab, recorrido = _lector_estricto(io.StringIO(texto), origen, formulas=formulas)
    filas, lineas = [], []
    for n, f in recorrido:
        filas.append(f)
        lineas.append(n)
    if miles:
        revisar_punto_de_miles(cab, filas, lineas, origen, ver=ver)
    return cab, filas, lineas


def revisar_punto_de_miles(cab, filas, lineas, origen="del CSV", ver=None):
    """FAILFAST: una columna solo numérica con punto de miles inequívoco (1.250.000, 1.250,50) o mezclado con enteros
    largos (78.000 junto a 1628100) detiene la lectura: leerlos como decimales los divide por mil en silencio (L46).
    Si el punto ya es decimal en la columna (12.5), 1.250 es un decimal y no miles (L49). ver(columna, valor) decide
    cómo sale el ejemplo en el mensaje (sin ver, tal cual)."""
    for j, col in enumerate(cab):
        crudos = [f[j] for f in filas]
        unidos = "\x1f".join(crudos)
        if "." not in unidos or _PUNTO_DECIMAL.search(unidos):
            continue    # sin puntos, o el punto ya es decimal en esta columna (12.5): 1.250 es un decimal, no miles
        valores = [v.strip() for v in crudos]
        if not all(_NUMERICO.match(v) for v in valores if v):
            continue    # columna de texto o de códigos (referencias, radicados): no es un monto
        con_punto = [i for i, v in enumerate(valores) if _PUNTO_DE_MILES.match(v)]
        if not con_punto:
            continue
        inequivoco = any(valores[i].count(".") > 1 or "," in valores[i] for i in con_punto)
        mezclado = any(_ENTERO_LARGO.match(v) for v in valores)
        if inequivoco or mezclado:
            detalle = " mezclados con números sin separador" if mezclado else ""
            ejemplo = valores[con_punto[0]]
            raise ValueError(f"la línea {lineas[con_punto[0]]} {origen}, columna «{col}», trae números con punto de miles "
                             f"(p. ej. {ver(col, ejemplo) if ver else ejemplo}){detalle}: leerlos como decimales los divide "
                             "por mil en silencio; hay que unificar el formato antes de leer")


def leer_csv(ruta):
    """Filas del CSV como diccionarios de texto, sin convertir nada, con las mismas detenciones que leer_tabla."""
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        cab, filas, _ = leer_tabla(fh.read())
    return [dict(zip(cab, f)) for f in filas]


class _Columna:
    """Lo que hace falta saber de una columna para la regla del punto de miles, sin guardar sus valores."""
    __slots__ = ("viva", "con_punto", "miles", "inequivoco", "entero_largo", "linea", "ejemplo")

    def __init__(self):
        self.viva, self.con_punto, self.miles, self.inequivoco, self.entero_largo = True, False, False, False, False
        self.linea, self.ejemplo = None, None    # el primer valor con punto de miles y su línea, para la detención

    def ver(self, v, linea=None):
        v = v.strip()
        if not v:
            return
        sin_signo = v[1:] if v[0] in "+-" else v
        if sin_signo.isdigit():
            if len(sin_signo) >= 4:
                self.entero_largo = True
            return
        if not _NUMERICO.match(v) or ("." in v and _PUNTO_DECIMAL.search(v)):
            self.viva = False   # texto o códigos, o el punto ya es decimal en esta columna: no es un monto con miles
            return
        if "." in v:
            self.con_punto = True
            if _PUNTO_DE_MILES.match(v):
                if not self.miles:
                    self.linea, self.ejemplo = linea, v
                self.miles = True
                if v.count(".") > 1 or "," in v:
                    self.inequivoco = True


def recorrer_csv(ruta):
    """Las mismas filas y detenciones que leer_csv, una por una: la memoria no crece con el tamaño de la fuente.
    Usa el mismo lector estricto que leer_tabla (línea vacía, campos de más o de menos, comilla sin cerrar, columnas
    repetidas, otro separador o una fórmula de Excel, con su línea).
    Para fuentes de millones de filas (leer_csv carga todo, unos 1,3 a 3,6 KB por fila, y la caja tiene 1.536 MB).
    La regla del punto de miles mira la columna completa: se cierra al final del recorrido, así que el código debe
    recorrer todas las filas (sumar, contar) para que una detención llegue; nunca cortar el recorrido a la mitad."""
    origen = "del CSV"
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        cab, recorrido = _lector_estricto(fh, origen)
        columnas = {col: _Columna() for col in cab}
        vivas = [(j, c) for j, c in enumerate(columnas.values())]
        for n, f in recorrido:
            if vivas:
                for j, c in vivas:
                    c.ver(f[j], n)
                if any(not c.viva for _, c in vivas):
                    vivas = [(j, c) for j, c in vivas if c.viva]
            yield dict(zip(cab, f))
    for col, c in columnas.items():
        if c.viva and c.con_punto and c.miles and (c.inequivoco or c.entero_largo):
            detalle = " mezclados con números sin separador" if c.entero_largo else ""
            raise ValueError(f"la línea {c.linea} {origen}, columna «{col}», trae números con punto de miles "
                             f"(p. ej. {c.ejemplo}){detalle}: leerlos como decimales los divide por mil en "
                             "silencio; hay que unificar el formato antes de leer")


def contar_registros(texto):
    """Registros de un CSV contados aparte del lector, con otro método: los saltos de línea fuera de comillas, menos
    el encabezado. Si no coincide con lo que leyó el lector, algo se partió, se pegó o trae comillas sueltas."""
    saltos = sum(parte.count("\n") for parte in texto.replace("\r\n", "\n").split('"')[0::2])
    lineas = saltos + (1 if texto and not texto.endswith("\n") else 0)
    return max(0, lineas - 1)


def aprox(a, b, tol=0.5):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


def suma(resultado, columna):
    return sum(float(f[columna]) for f in resultado if f.get(columna) is not None)


HIPOTESIS = {}


def hipotesis(id):
    """Registra la prueba de una hipótesis: fn(datos) -> {"valor": número, "linea_base": número o None, "detalle": texto}."""
    def decorar(fn):
        HIPOTESIS[id] = fn
        return fn
    return decorar
