from pathlib import Path
from typing import Dict, Any, Set


def collect_sources(
    root_dir: str = "aye",
    file_mask: str = "*.py",
    recursive: bool = True,
) -> Dict[str, str]:
    sources: Dict[str, str] = {}
    base_path = Path(root_dir).expanduser().resolve()

    if not base_path.is_dir():
        raise NotADirectoryError(f"'{root_dir}' is not a valid directory")

    # Choose iterator based on ``recursive`` flag
    iterator = base_path.rglob(file_mask) if recursive else base_path.glob(file_mask)

    for py_file in iterator:
        if not py_file.is_file():
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            rel_key = py_file.relative_to(base_path).as_posix()
            sources[rel_key] = content
        except UnicodeDecodeError:
            # Skip non‑UTF8 files
            print(f"   Skipping non‑UTF8 file: {py_file}")

    return sources


# ----------------------------------------------------------------------
# Example usage
def driver():
    py_dict = collect_sources()               # looks in ./aye
    # Or: py_dict = collect_py_sources("path/to/aye")

    # Show the keys (file names) that were collected
    print("Collected .py files:", list(py_dict.keys()))

    # Print the first 120 characters of each file (for demo)
    for name, txt in py_dict.items():
        print(f"\n--- {name} ---")
        print(txt[:120] + ("…" if len(txt) > 120 else ""))


if __name__ == "__main__":
    driver()


