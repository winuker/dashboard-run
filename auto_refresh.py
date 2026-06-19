import time
import json
import requests
import os

CLIENT_ID = "259075"
CLIENT_SECRET = "1e75833f800989c5fa7cf37010af9c7202802e1f"

TOKENS_FILE = "tokens.json"

def load_tokens():
    with open(TOKENS_FILE, "r") as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=4)

def refresh_tokens():
    tokens = load_tokens()

    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"]
    }

    response = requests.post(url, data=payload)
    new_tokens = response.json()

    save_tokens({
        "access_token": new_tokens["access_token"],
        "refresh_token": new_tokens["refresh_token"],
        "expires_at": new_tokens["expires_at"]
    })

    print("Tokens actualizados correctamente.")
    return new_tokens

def ensure_valid_token():
    tokens = load_tokens()
    now = int(time.time())

    if now >= tokens["expires_at"]:
        print("Token caducado. Refrescando…")
        return refresh_tokens()
    else:
        print("Token válido.")
        return tokens

if __name__ == "__main__":
    ensure_valid_token()
