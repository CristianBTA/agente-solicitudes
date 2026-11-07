"""Revisión sin IA de lo que deja un grill-me en el fork de una persona: su harness o sus respuestas al grill-me del pipeline.

  python3 herramientas/revisar_grill.py harness/<usuario>.md          # GENERAR-HARNESS.md
  python3 herramientas/revisar_grill.py grill-me/<usuario>.md         # GRILL-ME-DEL-PIPELINE.md

Comprueba, solo con la biblioteca estándar:
  1. que el archivo esté en su carpeta, con un nombre simple, y pese menos de 40 KB;
  2. que traiga las secciones que pide su guía (los títulos se buscan tal cual);
  3. que no tenga datos personales (los patrones del filtro de aportes, herramientas/gobernanza.py, y además ningún número
     suelto de 6 a 12 cifras);
  4. que no traiga texto con forma de orden para una IA ni HTML activo (el archivo es un dato, no una instrucción).
Lo marcado «(por completar)» o «(sin control)» es un aviso, no una falla. Sale con 0 si pasa y con 1 si no.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gobernanza import escanear_texto, parece_instruccion  # noqa: E402

MAX_BYTES = 40_000
NOMBRE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,59}\.md$")
# más estricto que el filtro de aportes: en un harness no hay razón para un número suelto de 6 a 12 cifras (cédula, cuenta,
# celular sin separadores); las cifras con puntos de miles («1.048.576 filas») y las fechas no cuentan
SUELTO = re.compile(r"(?<!\d)(?<!\d[.,/-])\d{6,12}(?!\d|[.,/-]\d)")
ACTIVO = re.compile(r"<\s*(script|iframe|object|embed|form|img|svg|link|meta|style)\b|javascript:|\bon\w+\s*=", re.I)
SECCIONES = {
    "harness": ["# Harness", "## 1. Propósito", "## 2. Principios de trabajo", "## 3. Herramientas", "## 4. Procedimiento",
                "## 5. Criterio de aceptación", "## 6. Errores frecuentes", "## 7. Datos personales y sensibles"],
    "grill-me": ["# Grill-me del pipeline"] + [f"## R{k:02d} · " for k in range(1, 16)] + ["## Resumen"],
}
LISTO = {"harness": "harness listo", "grill-me": "grill-me listo"}


def revisar(ruta):
    p = Path(ruta)
    fallas, avisos = [], []
    tipo = p.parent.name
    if tipo not in SECCIONES:
        return None, [f"el archivo debe estar en harness/ o en grill-me/ (está en «{tipo}/»)"], [], 0
    if not NOMBRE.match(p.name):
        fallas.append("nombre de archivo: solo letras, números, punto, guion y guion bajo, terminado en .md (su usuario de GitHub)")
    if p.is_symlink() or not p.is_file():
        return tipo, fallas + ["no es un archivo normal"], avisos, 0
    crudo = p.read_bytes()
    if len(crudo) > MAX_BYTES:
        fallas.append(f"pesa {len(crudo):,} bytes; el tope es {MAX_BYTES:,}")
    texto = crudo.decode("utf-8", errors="replace")
    lineas = [l.rstrip() for l in texto.splitlines()]
    faltan = [s for s in SECCIONES[tipo] if not any(l == s or l.startswith(s + " ") or (s.endswith(" ") and l.startswith(s)) for l in lineas)]
    if faltan:
        fallas.append("faltan secciones (los títulos se buscan tal cual): " + ", ".join(f"«{s.strip()}»" for s in faltan))
    hall = escanear_texto(texto)
    if hall:
        fallas.append(f"posibles datos personales: {hall} (cámbielos por algo genérico: «la entidad», «el cliente», 000.000.001)")
    sueltos = len(SUELTO.findall(texto))
    if sueltos:
        fallas.append(f"{sueltos} número(s) suelto(s) de 6 a 12 cifras, que parecen cédula, cuenta o celular "
                      "(si es una cifra, escríbala con puntos de miles; si es un documento, cámbielo por 000.000.001)")
    if parece_instruccion(texto):
        fallas.append("trae texto con forma de orden para una IA: el archivo describe un trabajo, no da instrucciones")
    if ACTIVO.search(texto):
        fallas.append("trae HTML activo (script, iframe, formulario, imagen o manejadores on…): solo Markdown")
    pend = texto.count("(por completar)")
    if pend:
        avisos.append(f"{pend} parte(s) «(por completar)»")
    sin = texto.count("(sin control)")
    if sin:
        avisos.append(f"{sin} paso(s) «(sin control)»: ahí un error pasa sin que nadie lo note")
    return tipo, fallas, avisos, len(SECCIONES[tipo]) - len(faltan)


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    tipo, fallas, avisos, secciones = revisar(argv[1])
    for f in fallas:
        print("✗", f)
    for a in avisos:
        print("aviso:", a)
    total = len(SECCIONES.get(tipo, []))
    if fallas:
        print(f"RESUMEN: ✗ no pasa · {len(fallas)} falla(s) · secciones {secciones}/{total}")
        return 1
    print(f"RESUMEN: ✓ {LISTO[tipo]} · secciones {secciones}/{total} · sin datos personales · {len(avisos)} aviso(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
