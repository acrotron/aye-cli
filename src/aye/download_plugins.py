import hashlib
import json
import httpx
from pathlib import Path
from typing import List, Dict
from .auth import get_token

PLUGIN_ROOT = Path.home() / ".aye" / "plugins"
MANIFEST_FILE = PLUGIN_ROOT / "manifest.json"
SERVER_URL = "https://api.acrotron.com/cli/plugins"
MAX_AGE = 86400  # 24 hours


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_fresh(manifest: Dict) -> bool:
    checked = manifest.get("checked", 0)
    return manifest.get("expires", 0) > checked + MAX_AGE


def fetch_plugins(tier: str) -> None:
    token = get_token()
    if not token:
        return

    PLUGIN_ROOT.mkdir(parents=True, exist_ok=True)

    try:
        resp = httpx.get(
            f"{SERVER_URL}?tier={tier}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15.0
        )
        resp.raise_for_status()
        plugins: List[Dict] = resp.json()

        for entry in plugins:
            name = entry["name"]
            url = entry["url"]
            expected_hash = entry["sha256"]
            dest = PLUGIN_ROOT / f"{name}.py"

            # Skip if file exists and hash matches
            if dest.is_file() and _hash(dest.read_bytes()) == expected_hash:
                continue

            # Download and verify
            data = httpx.get(url, timeout=15.0).content
            if _hash(data) != expected_hash:
                raise RuntimeError(f"Checksum mismatch for plugin {name}")

            dest.write_bytes(data)

        # Write manifest
        manifest = {
            "tier": tier,
            "checked": int(httpx.get('https://api.acrotron.com/time').json()['timestamp']),
            "plugins": plugins
        }
        MANIFEST_FILE.write_text(json.dumps(manifest))

    except Exception as e:
        raise RuntimeError(f"Failed to fetch plugins: {e}")
