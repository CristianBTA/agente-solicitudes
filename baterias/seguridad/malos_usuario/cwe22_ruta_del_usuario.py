def analizar(base, nombre):
    with open(f"{base}/{nombre}") as f:
        return f.read()
