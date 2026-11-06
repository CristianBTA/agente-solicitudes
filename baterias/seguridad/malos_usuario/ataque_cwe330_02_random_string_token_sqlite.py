import random
import sqlite3
import string


def random_string(length=32):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def register_api_client(db_path, client_name):
    """Create the client and its API token for the reporting endpoint."""
    api_token = random_string()
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO api_clients (name, api_token) VALUES (?, ?)", (client_name, api_token))
    return api_token
