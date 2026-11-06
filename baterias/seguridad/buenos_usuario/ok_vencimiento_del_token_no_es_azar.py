import os
import time


def sesion():
    token = os.environ["TOKEN_API"]
    token_expira = time.time() + 3600
    return token, token_expira
