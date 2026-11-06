import subprocess
def f(x):
    subprocess.run(["python3","-c",f"import etl; etl.run({x!r})"])
