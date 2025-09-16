# --------------------------------------------------------------
# snapshot.py – batch snapshot utilities (single‑timestamp folder)
# --------------------------------------------------------------
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

SNAP_ROOT = Path(".aye/snapshots").resolve()


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------
def _ensure_batch_dir(ts: str) -> Path:
    """Create (or return) the batch directory for a given timestamp."""
    batch_dir = SNAP_ROOT / "batches" / ts
    batch_dir.mkdir(parents=True, exist_ok=True)
    return batch_dir


def _list_all_snapshots_with_metadata():
    """List all snapshots in descending order with file names from metadata."""
    batches_root = SNAP_ROOT / "batches"
    if not batches_root.is_dir():
        return []

    timestamps = [p.name for p in batches_root.iterdir() if p.is_dir()]
    timestamps.sort(reverse=True)
    result = []
    for ts in timestamps:
        meta_path = batches_root / ts / "metadata.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            files = [Path(entry["original"]).name for entry in meta["files"]]
            files_str = ",".join(files)
            result.append(f"{ts}  {files_str}")
        else:
            result.append(f"{ts}  (metadata missing)")
    return result


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def create_snapshot(file_paths: List[Path]) -> str:
    """
    Snapshot the **current** contents of the given files.

    Returns the timestamp string that identifies the batch.
    """
    if not file_paths:
        raise ValueError("No files supplied for snapshot")

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    batch_dir = _ensure_batch_dir(ts)

    meta_entries: List[Dict[str, Any]] = []

    for src_path in file_paths:
        src_path = src_path.resolve()
        dest_path = batch_dir / src_path.name

        if src_path.is_file():
            shutil.copy2(src_path, dest_path)   # copy old content
        else:
            dest_path.touch()                    # placeholder for a new file

        meta_entries.append(
            {"original": str(src_path), "snapshot": str(dest_path)}
        )

    meta = {"timestamp": ts, "files": meta_entries}
    (batch_dir / "metadata.json").write_text(json.dumps(meta, indent=2))

    return ts


def list_snapshots(file: Path | None = None) -> List[str]:
    """Return all batch‑snapshot timestamps, newest first, or snapshots for a specific file."""
    if file is None:
        return _list_all_snapshots_with_metadata()
    
    batches_root = SNAP_ROOT / "batches"
    if not batches_root.is_dir():
        return []

    snapshots = []
    for batch_dir in batches_root.iterdir():
        if batch_dir.is_dir():
            meta_path = batch_dir / "metadata.json"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                for entry in meta["files"]:
                    if Path(entry["original"]) == file.resolve():
                        snapshots.append((batch_dir.name, entry["snapshot"]))
    snapshots.sort(key=lambda x: x[0], reverse=True)
    return snapshots


def restore_snapshot(timestamp: str | None = None) -> None:
    """
    Restore *all* files from a batch snapshot.
    If ``timestamp`` is omitted the most recent snapshot is used.
    """
    if timestamp is None:
        timestamps = list_snapshots()
        if not timestamps:
            raise ValueError("No snapshots found")
        timestamp = timestamps[0]               # most recent

    batch_dir = SNAP_ROOT / "batches" / timestamp
    if not batch_dir.is_dir():
        raise ValueError(f"No snapshot found for timestamp {timestamp}")

    meta_file = batch_dir / "metadata.json"
    if not meta_file.is_file():
        raise ValueError(f"Metadata missing for snapshot {timestamp}")

    meta = json.loads(meta_file.read_text())

    for entry in meta["files"]:
        original = Path(entry["original"])
        snapshot = Path(entry["snapshot"])
        if not snapshot.is_file():
            print(f"Warning: snapshot missing – {snapshot}")
            continue
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snapshot, original)


# ------------------------------------------------------------------
# Helper that combines snapshot + write‑new‑content
# ------------------------------------------------------------------
def apply_updates(updated_files: List[Dict[str, str]]) -> str:
    """
    1️⃣ Take a snapshot of the *current* files.
    2️⃣ Write the new contents supplied by the LLM.
    Returns the batch timestamp (useful for UI feedback).
    """
    # ---- 1️⃣ Build a list of Path objects for the files that will change ----
    file_paths: List[Path] = [
        Path(item["file_name"])
        for item in updated_files
        if "file_name" in item and "file_content" in item
    ]

    # ---- 2️⃣ Snapshot the *existing* state ----
    batch_ts = create_snapshot(file_paths)

    # ---- 3️⃣ Overwrite with the new content ----
    for item in updated_files:
        fp = Path(item["file_name"])
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(item["file_content"])

    return batch_ts


def driver():
    list_snapshots()


if __name__ == "__main__":
    driver()
