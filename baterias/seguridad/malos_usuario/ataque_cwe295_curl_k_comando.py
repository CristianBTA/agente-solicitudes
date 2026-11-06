import subprocess

import pandas as pd


def bajar(url):
    subprocess.run(["curl", "-skL", "-o", "ventas.csv", url], check=True)
    return pd.read_csv("ventas.csv")
