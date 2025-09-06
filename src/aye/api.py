import json
from typing import Any, Dict

import httpx
from .auth import get_token

# -------------------------------------------------
# 👉  EDIT THIS TO POINT TO YOUR SERVICE
# -------------------------------------------------
BASE_URL = "https://api.example.com/v1"
TIMEOUT = 30.0


def _auth_headers() -> Dict[str, str]:
    token = get_token()
    if not token:
        raise RuntimeError("No auth token – run `aye login` first.")
    return {"Authorization": f"Bearer {token}"}


def generate(
    prompt: str,
    filename: str | None = None,
    mode: str = "replace",
) -> Dict[str, Any]:
    """
    Send a prompt to the backend and return the JSON response.
    Expected response shape:
        {
            "generated_code": "...",
            "usage": {"input_tokens": …, "output_tokens": …}
        }
    """
    payload = {"prompt": prompt, "mode": mode, "filename": filename}
    url = f"{BASE_URL}/generate"

    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(url, json=payload, headers=_auth_headers())
        resp.raise_for_status()
        return resp.json()

