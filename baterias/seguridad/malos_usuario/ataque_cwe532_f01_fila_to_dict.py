import logging

import pandas as pd

logger = logging.getLogger(__name__)


def cargar_afiliados():
    df = pd.read_csv("afiliados.csv", usecols=["cedula", "nombre_completo", "correo", "valor_cuota"], dtype=str)
    cuotas = []
    for idx, row in df.iterrows():
        try:
            cuotas.append(float(row["valor_cuota"]))
        except ValueError:
            logger.warning("Fila %s rechazada, valor_cuota no numérico: %s", idx, row.to_dict())
    return cuotas
