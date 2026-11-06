import logging
import os

import pandas as pd
import psycopg2

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]


def leer_contratos():
    logger.info("Conectando a %s", DATABASE_URL)
    with psycopg2.connect(DATABASE_URL) as conn:
        df = pd.read_sql("SELECT id_contrato, valor FROM contratos", conn)
    logger.info("Filas leídas: %d", len(df))
    return df
