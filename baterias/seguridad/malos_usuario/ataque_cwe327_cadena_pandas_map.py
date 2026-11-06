import hashlib, pandas as pd
def anon(x):
    return hashlib.sha256(x.encode()).hexdigest()
df = pd.read_csv("a.csv")
df["cedula"] = df["cedula"].astype(str).map(anon)
df["correo"] = df["correo"].astype(str).str.lower().apply(lambda v: hashlib.md5(v.encode(), usedforsecurity=False).hexdigest())
