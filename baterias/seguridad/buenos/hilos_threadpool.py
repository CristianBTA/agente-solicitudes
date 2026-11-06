from concurrent.futures import ThreadPoolExecutor
def analizar(datos):
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(len, [[1], [2, 3]]))
    return []
