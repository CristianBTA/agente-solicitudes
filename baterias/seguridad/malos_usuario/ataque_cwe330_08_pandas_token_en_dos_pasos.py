import numpy as np
import pandas as pd


def preparar_carga_portal(clientes: pd.DataFrame) -> pd.DataFrame:
    """Deja lista la tabla del portal: cada cliente entra con un token en la URL."""
    rng = np.random.default_rng(42)
    valores = rng.integers(0, 2**63 - 1, size=len(clientes), dtype=np.int64)
    salida = clientes[["id_cliente", "razon_social"]].copy()
    salida["token_portal"] = [format(v, "016x") for v in valores]
    return salida
