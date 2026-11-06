import subprocess

import pandas as pd

subprocess.run(
    ["curl", "-sS", "-u", "ingesta_batch:K8x9mP2qLw", "-o", "contratos.csv", "https://repo-estadistica.interna/contratos.csv"],
    check=True,
)
df = pd.read_csv("contratos.csv")
print(df.shape)
