import re,subprocess
def f(x):
    if not re.fullmatch(r".+", x):
        raise ValueError
    subprocess.run(f"gzip {x}",shell=True)
