import json
from typing import Any, Dict

import httpx
from .auth import get_token

# -------------------------------------------------
# 👉  EDIT THIS TO POINT TO YOUR SERVICE
# -------------------------------------------------
BASE_URL = "https://api.acrotron.com"
TIMEOUT = 30.0


def _auth_headers() -> Dict[str, str]:
    token = "aye_XXX" #get_token()
    if not token:
        raise RuntimeError("No auth token – run `aye login` first.")
    return {"Authorization": f"Bearer {token}"}


def cli_invoke(user_id="v@acrotron.com", chat_id=-1, message="", source_files={}):
    payload = {"user_id": user_id, "chat_id": chat_id, "message": message, "source_files": source_files}

    url = f"{BASE_URL}/invoke_cli"

    with httpx.Client(timeout=TIMEOUT, verify=True) as client:
        resp = client.post(url, json=payload, headers=_auth_headers())
        resp.raise_for_status()
        return resp.json()
