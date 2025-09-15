import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

SNAP_ROOT = Path(".aye/snapshots").resolve()


def _snapshot_dir(file_path: Path) -> Path:
    """Directory that will hold snapshots for *file_path*.
    Snapshots are stored in `.aye/snapshots` relative to the current directory."""
    file_path = file_path.resolve()  # Ensure absolute path for safety
    cwd = Path.cwd()
    try:
        rel = file_path.relative_to(cwd)
    except ValueError:
        # If file is not under cwd, use the full absolute path (relative to root)
        rel = file_path
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


def update_files_with_snapshots(updated_files: List[dict]) -> None:
    """Create snapshots for all files mentioned and update their content.

    Args:
        updated_files: List of dictionaries with 'file_name' and 'file_content' keys
    """
    for file_info in updated_files:
        file_name = file_info.get("file_name")
        file_content = file_info.get("file_content")

        if not file_name or file_content is None:
            print(f"Warning: Skipping invalid file info: {file_info}")
            continue

        file_path = Path(file_name)

        # Create snapshot before updating
        try:
            create_snapshot(file_path)
        except FileNotFoundError:
            # If file doesn't exist, ensure its parent directory exists and create an empty file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("")
            create_snapshot(file_path)
        except Exception as e:
            print(f"Warning: Failed to create snapshot for {file_name}: {e}")
            continue

        # Update file content
        try:
            file_path.write_text(file_content)
        except Exception as e:
            print(f"Error: Failed to update {file_name}: {e}")
