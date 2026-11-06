import subprocess

def exportar_capa_geografica(nombre_capa):
    comando = f"ogr2ogr -f GeoJSON /tmp/{nombre_capa}.json /geodatos/{nombre_capa}.shp"
    subprocess.call(comando, shell=True)
    return True
