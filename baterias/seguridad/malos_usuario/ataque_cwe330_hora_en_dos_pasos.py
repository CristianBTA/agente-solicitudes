import hashlib, time, datetime as dt
def crear_token_reset(uid):
    ahora = dt.datetime.now().isoformat()
    base = f"{uid}|{ahora}"
    return hashlib.md5(base.encode(), usedforsecurity=False).hexdigest()
def token_sesion(uid):
    ts = str(time.time())
    return hashlib.sha256((uid + ts).encode()).hexdigest()
