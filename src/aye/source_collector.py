from pathlib import Path
from typing import Dict, Any, Set


def _is_hidden(path: Path) -> bool:
    """Return True if *path* or any of its ancestors is a hidden directory.

    Hidden directories are those whose name starts with a dot (".").
    """
    return any(part.startswith(".") for part in path.parts)


def _load_ignore_patterns(root_path: Path) -> list[str]:
    """Load ignore patterns from .ayeignore file in the root directory."""
    ignore_file = root_path / ".ayeignore"
    if not ignore_file.exists():
        return []
    
    try:
        patterns = ignore_file.read_text(encoding="utf-8").splitlines()
        # Filter out empty lines and comments
        return [pattern.strip() for pattern in patterns 
                if pattern.strip() and not pattern.strip().startswith("#")]
    except Exception:
        # If we can't read the file, proceed without ignore patterns
        return []


def _matches_ignore_pattern(path: Path, ignore_patterns: list[str], base_path: Path) -> bool:
    """Check if a path matches any of the ignore patterns."""
    try:
        relative_path = path.relative_to(base_path)
    except ValueError:
        # Path is not relative to base_path, shouldn't happen but be safe
        return False
    
    path_str = relative_path.as_posix()
    
    for pattern in ignore_patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            dir_pattern = pattern.rstrip("/")
            # Check if any part of the path matches the directory pattern
            if any(part == dir_pattern for part in relative_path.parts):
                return True
        else:
            # For file patterns, check if the file name or full path matches
            if relative_path.match(pattern):
                return True
            # Also check just the file name for simpler patterns
            if path.name == pattern or Path(path.name).match(pattern):
                return True
    
    return False


def collect_sources(
    root_dir: str = ".",
    file_mask: str = "*.py",
    recursive: bool = True,
) -> Dict[str, str]:
    sources: Dict[str, str] = {}
    base_path = Path(root_dir).expanduser().resolve()

    if not base_path.is_dir():
        raise NotADirectoryError(f"'{root_dir}' is not a valid directory")

    # Load ignore patterns from .ayeignore file
    ignore_patterns = _load_ignore_patterns(base_path)

    # Choose iterator based on ``recursive`` flag
    iterator = base_path.rglob(file_mask) if recursive else base_path.glob(file_mask)

    for py_file in iterator:
        # Skip hidden subfolders (any part of the path starting with '.')
        if _is_hidden(py_file.relative_to(base_path)):
            continue
        
        # Skip files that match ignore patterns
        if _matches_ignore_pattern(py_file, ignore_patterns, base_path):
            continue
            
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
