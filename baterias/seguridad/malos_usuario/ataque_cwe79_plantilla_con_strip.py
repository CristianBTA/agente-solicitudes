import pandas as pd

FILA = """
<tr>
  <td>{entidad}</td>
  <td>{objeto}</td>
  <td>{valor}</td>
</tr>
""".strip()


def filas_html(ruta_csv):
    df = pd.read_csv(ruta_csv)
    return "\n".join(FILA.format(entidad=f.entidad, objeto=f.objeto, valor=f.valor) for f in df.itertuples())
