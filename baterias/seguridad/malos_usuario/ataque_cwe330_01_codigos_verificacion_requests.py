import os
import random

import pandas as pd
import requests

SMS_URL = "https://sms.example.invalid/v1/messages"


def send_verification_codes(csv_path):
    """Send a verification code to every new contractor and return the codes to load into the portal."""
    users = pd.read_csv(csv_path, dtype=str)
    codes = {}
    for _, row in users.iterrows():
        code = random.randint(100000, 999999)
        resp = requests.post(
            SMS_URL,
            json={"to": row["phone"], "text": f"Your verification code is {code}"},
            headers={"Authorization": f"Bearer {os.environ['SMS_API_KEY']}"},
            timeout=10,
        )
        resp.raise_for_status()
        codes[row["user_id"]] = code
    return codes
