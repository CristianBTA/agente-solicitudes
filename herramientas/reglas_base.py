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
        for col, v in f.items():
            if v.lstrip().startswith("="):
                raise ValueError(f"la línea {i}, columna «{col}», trae una fórmula de Excel como texto, no su valor: "
                                 "hay que exportar los valores (Pegado especial → Valores) antes de leer")
            if col and ("fecha" in col.lower() or col.lower().endswith(("_date", "date"))):
                val = v.strip().split("T")[0]
                if "-" in val:
                    partes = val.split("-")
                    if len(partes) == 3 and partes[0].isdigit() and len(partes[0]) == 4 and partes[1].isdigit() and partes[2].isdigit():
                        mes, dia = int(partes[1]), int(partes[2])
                        if mes < 1 or mes > 12:
                            raise ValueError(f"la línea {i}, columna «{col}», trae una fecha con mes inválido ({mes}): «{v}»")
                        if dia < 1 or dia > 31:
                            raise ValueError(f"la línea {i}, columna «{col}», trae una fecha con día inválido ({dia}): «{v}»")
                elif "/" in val:
                    partes = val.split("/")
                    if len(partes) == 3 and partes[2].isdigit() and len(partes[2]) == 4 and partes[0].isdigit() and partes[1].isdigit():
                        p0, p1 = int(partes[0]), int(partes[1])
                        if p0 > 12 and p1 > 12:
                            raise ValueError(f"la línea {i}, columna «{col}», trae una fecha con mes imposible (ambos valores > 12): «{v}»")
                        if p0 < 1 or p1 < 1 or p0 > 31 or p1 > 31:
                            raise ValueError(f"la línea {i}, columna «{col}», trae una fecha con día o mes fuera de rango: «{v}»")
    for col in cab:
        valores = [f[col].strip() for f in filas]
        if not any("." in v for v in valores):
            continue
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
