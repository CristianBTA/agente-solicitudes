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


def leer_csv(ruta):
    """Filas del CSV como diccionarios de texto, sin convertir nada. FAILFAST: una comilla sin cerrar o una
    fila con más o menos campos que el encabezado o una celda con una fórmula de Excel como texto («=DAY(J2)»)
    detienen la lectura; nunca se leen en silencio."""
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        lector = csv.DictReader(fh, strict=True)
        filas = list(lector)
        cab = lector.fieldnames or []
    if len(cab) == 1 and any(sep in cab[0] for sep in (";", "\t", "|")):
        raise ValueError(f"el encabezado tiene una sola columna con «;», tabulador o «|»: el separador no es la coma")
    for i, f in enumerate(filas, 2):
        if None in f or any(v is None for v in f.values()):
            raise ValueError(f"la línea {i} del CSV no tiene el mismo número de campos que el encabezado")
        if "=" in "\x1f".join(f.values()):    # la revisión celda por celda solo donde hay un «=» (escala a millones de filas)
            for col, v in f.items():
                if v.lstrip().startswith("="):
                    raise ValueError(f"la línea {i}, columna «{col}», trae una fórmula de Excel como texto, no su valor: "
                                     "hay que exportar los valores (Pegado especial → Valores) antes de leer")
    for col, crudos in zip(cab, zip(*(f.values() for f in filas))):
        unidos = "\x1f".join(crudos)
        if "." not in unidos or _PUNTO_DECIMAL.search(unidos):
            continue    # sin puntos, o el punto ya es decimal en esta columna (12.5): 1.250 es un decimal, no miles
        valores = [v.strip() for v in crudos]
        if not all(_NUMERICO.match(v) for v in valores if v):
            continue    # columna de texto o de códigos (referencias, radicados): no es un monto
        con_punto = [v for v in valores if _PUNTO_DE_MILES.match(v)]
        if not con_punto:
            continue
        inequivoco = any(v.count(".") > 1 or "," in v for v in con_punto)
        mezclado = any(_ENTERO_LARGO.match(v) for v in valores)
        if inequivoco or mezclado:
            detalle = " mezclados con números sin separador" if mezclado else ""
            raise ValueError(f"la columna «{col}» trae números con punto de miles (p. ej. 1.250.000){detalle}: leerlos como decimales "
                             "los divide por mil en silencio; hay que unificar el formato antes de leer")
    return filas



class _Columna:
    """Lo que hace falta saber de una columna para la regla del punto de miles, sin guardar sus valores."""
    __slots__ = ("viva", "con_punto", "miles", "inequivoco", "entero_largo")

    def __init__(self):
        self.viva, self.con_punto, self.miles, self.inequivoco, self.entero_largo = True, False, False, False, False

    def ver(self, v):
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
                self.miles = True
                if v.count(".") > 1 or "," in v:
                    self.inequivoco = True


def recorrer_csv(ruta):
    """Las mismas filas y detenciones que leer_csv, una por una: la memoria no crece con el tamaño de la fuente.
    Para fuentes de millones de filas (leer_csv carga todo, unos 1,3 a 3,6 KB por fila, y la caja tiene 1.536 MB).
    La regla del punto de miles mira la columna completa: se cierra al final del recorrido, así que el código debe
    recorrer todas las filas (sumar, contar) para que una detención llegue; nunca cortar el recorrido a la mitad."""
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        lector = csv.DictReader(fh, strict=True)
        cab = lector.fieldnames or []
        if len(cab) == 1 and any(sep in cab[0] for sep in (";", "\t", "|")):
            raise ValueError(f"el encabezado tiene una sola columna con «;», tabulador o «|»: el separador no es la coma")
        columnas = {col: _Columna() for col in cab}
        vivas = list(columnas.items())
        for i, f in enumerate(lector, 2):
            if None in f or any(v is None for v in f.values()):
                raise ValueError(f"la línea {i} del CSV no tiene el mismo número de campos que el encabezado")
            if "=" in "\x1f".join(f.values()):
                for col, v in f.items():
                    if v.lstrip().startswith("="):
                        raise ValueError(f"la línea {i}, columna «{col}», trae una fórmula de Excel como texto, no su valor: "
                                         "hay que exportar los valores (Pegado especial → Valores) antes de leer")
            if vivas:
                for col, c in vivas:
                    c.ver(f[col])
                if any(not c.viva for _, c in vivas):
                    vivas = [(col, c) for col, c in vivas if c.viva]
            yield f
    for col, c in columnas.items():
        if c.viva and c.con_punto and c.miles and (c.inequivoco or c.entero_largo):
            detalle = " mezclados con números sin separador" if c.entero_largo else ""
            raise ValueError(f"la columna «{col}» trae números con punto de miles (p. ej. 1.250.000){detalle}: leerlos como decimales "
                             "los divide por mil en silencio; hay que unificar el formato antes de leer")

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
