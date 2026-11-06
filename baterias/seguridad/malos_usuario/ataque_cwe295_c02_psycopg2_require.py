import os

import pandas as pd
import psycopg2


def traer_ventas(desde):
    conexion = psycopg2.connect(
        host=os.environ["PG_HOST"],
        dbname="ventas",
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        sslmode="require",
    )
    with conexion:
        return pd.read_sql("SELECT region, total FROM ventas WHERE fecha >= %s", conexion, params=(desde,))
