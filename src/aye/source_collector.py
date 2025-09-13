from pathlib import Path
from typing import Dict


def collect_sources(root_dir="aye"):
    sources: Dict[str, str] = {}

    # Resolve the directory – works with relative or absolute paths
    base_path = Path(root_dir).expanduser().resolve()

    if not base_path.is_dir():
        raise NotADirectoryError(f"'{root_dir}' is not a valid directory")

    # Iterate over all .py files (non‑recursive)
    for py_file in base_path.glob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            sources[py_file.name] = content
        except UnicodeDecodeError:
            # Skip files that aren't valid UTF‑8; you could log or raise instead
            print(f"⚠️  Skipping non‑UTF8 file: {py_file}")

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


