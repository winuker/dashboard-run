import time
import json
import requests
import os

TOKENS_FILE = "tokens.json"

CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]


def load_tokens():
    if not os.path.exists(TOKENS_FILE):
        # Si no existe, creamos uno básico solo con expires_at pasado
        data = {
            "access_token": "",
            "expires_at": 0
        }
        with open(TOKENS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return data

    with open(TOKENS_FILE, "r") as f:
        return json.load(f)


def save_tokens(tokens):
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=4)


def refresh_tokens():
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }

    response = requests.post(url, data=payload)
    response.raise_for_status()
    new_tokens = response.json()

    save_tokens({
        "access_token": new_tokens["access_token"],
        "expires_at": new_tokens["expires_at"]
    })

    print("Tokens actualizados correctamente.")
    return new_tokens


def ensure_valid_token():
    tokens = load_tokens()
    now = int(time.time())

    if now >= tokens.get("expires_at", 0) or not tokens.get("access_token"):
        print("Token caducado o inexistente. Refrescando…")
        return refresh_tokens()
    else:
        print("Token válido.")
        return tokens


if __name__ == "__main__":
    ensure_valid_token()
