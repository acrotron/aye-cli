import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

SNAP_ROOT = Path.home() / ".aye_snapshots"


def _snapshot_dir(file_path: Path) -> Path:
    """Directory that will hold snapshots for *file_path*."""
    rel = file_path.relative_to(file_path.anchor)   # strip leading “/”
    return SNAP_ROOT / rel.parent


def create_snapshot(file_path: Path) -> Path:
    """Copy the file to a timestamped backup and write a metadata JSON."""
    if not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    snap_dir = _snapshot_dir(file_path)
    snap_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    snap_file = snap_dir / f"{file_path.name}.{ts}.bak"
    shutil.copy2(file_path, snap_file)

    meta = {
        "original": str(file_path),
        "snapshot": str(snap_file),
        "timestamp": ts,
    }
    (snap_dir / f"{file_path.name}.{ts}.json").write_text(json.dumps(meta))
    return snap_file


def list_snapshots(file_path: Path) -> List[Tuple[str, Path]]:
    """Return a list of (timestamp, snapshot_path) sorted newest‑first."""
    snap_dir = _snapshot_dir(file_path)
    if not snap_dir.is_dir():
        return []

    snaps = []
    for meta_file in snap_dir.glob(f"{file_path.name}.*.json"):
        meta = json.loads(meta_file.read_text())
        snaps.append((meta["timestamp"], Path(meta["snapshot"])))
    snaps.sort(reverse=True)
    return snaps


def restore_snapshot(file_path: Path, timestamp: str) -> None:
    """Replace *file_path* with the snapshot that matches *timestamp*."""
    for ts, snap_path in list_snapshots(file_path):
        if ts == timestamp:
            shutil.copy2(snap_path, file_path)
            return
    raise ValueError(f"No snapshot for {file_path} with timestamp {timestamp}")

