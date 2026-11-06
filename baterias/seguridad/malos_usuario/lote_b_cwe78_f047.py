import subprocess

def extraer_audio_declaracion(archivo_video, archivo_audio):
    cadena = f"ffmpeg -i {archivo_video} -vn -ar 16000 {archivo_audio}"
    return subprocess.run(cadena, shell=True).returncode
