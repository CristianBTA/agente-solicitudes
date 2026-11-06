import requests


def tarjeta_dataset(dataset_id):
    r = requests.get(f"https://datos.example/api/views/{dataset_id}.json", timeout=30)
    r.raise_for_status()
    meta = r.json()
    descripcion = "Sin descripción"
    if meta.get("description"):
        descripcion = meta["description"]
    return f"<div class='tarjeta'><h3>Conjunto de datos</h3><p>{descripcion}</p></div>"
