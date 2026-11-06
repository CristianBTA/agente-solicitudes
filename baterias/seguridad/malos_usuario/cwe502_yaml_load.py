import yaml
def analizar(ruta):
    with open(ruta) as f:
        return yaml.load(f, Loader=yaml.Loader)
