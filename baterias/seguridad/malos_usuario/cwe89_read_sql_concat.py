import pandas as pd
def analizar(con, entidad):
    return pd.read_sql("SELECT * FROM c WHERE e = '" + entidad + "'", con)
