import json
import subprocess
import re
from rich import print as rprint
from pathlib import Path
from rich.console import Console

from typing import Optional, List, Dict

from .api import cli_invoke
from .source_collector import collect_sources
from .snapshot import restore_snapshot, list_snapshots, create_snapshot
from .config import get_value, set_value, delete_value, list_config


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mK]")


# Create a global console instance for diff output
_diff_console = Console(force_terminal=True, markup=False, color_system="standard")

# Authentication functions (from auth.py)
def handle_login(url: str) -> None:
    """Configure username and token for authenticating with the aye service."""
    from .auth import login_flow
    login_flow(url)


def handle_logout() -> None:
    """Remove the stored aye credentials."""
    from .auth import delete_token
    delete_token()
    rprint("\U0001f510 Token removed.")


# One-shot generation function
def handle_generate_cmd(prompt: str, file: Optional[Path], mode: str) -> None:
    """
    Send a single prompt to the backend.  If `file` is supplied,
    the file is snapshotted first, then overwritten/appended.
    """
    if file:
        create_snapshot([file])          # ← undo point

    resp = cli_invoke(message=prompt, filename=str(file) if file else None, mode=mode)
    code = resp.get("generated_code", "")

    if file:
        file.write_text(code)
        rprint(f"\u2705 {file} updated (snapshot taken)")
    else:
        rprint(code)


# Chat function
def handle_chat(root: Path, file_mask: str) -> None:
    """Start an interactive REPL. Use /exit or Ctrl‑D to leave."""
    from types import SimpleNamespace
    from .repl import chat_repl
    
    if root is None:
        root = Path.cwd()
    
    conf = SimpleNamespace()
    conf.root = root
    conf.file_mask = file_mask
    chat_repl(conf)


# Snapshot functions
def handle_history_cmd(file: Optional[Path]) -> None:
    """Show timestamps of saved snapshots for *file* or all snapshots if no file provided."""
    snapshots = list_snapshots(file)
    if not snapshots:
        print("No snapshots found.")
        return
    for snapshot in snapshots:
        print(snapshot)


def handle_snap_show_cmd(file: Path, ts: str) -> None:
    """Print the contents of a specific snapshot."""
    for snap_ts, snap_path in list_snapshots(file):
        if snap_ts == ts:
            print(Path(snap_path).read_text())
            return
    rprint("Snapshot not found.", err=True)


def handle_restore_cmd(ts: Optional[str]) -> None:
    """Replace all files with the latest snapshot or specified snapshot."""
    try:
        restore_snapshot(ts)
        if ts:
            rprint(f"\u2705 All files restored to {ts}")
        else:
            rprint(f"\u2705 All files restored to latest snapshot")
    except Exception as exc:
        rprint(f"Error: {exc}", err=True)


def _is_valid_command(command: str) -> bool:
    """Check if a command exists in the system using bash's command -v"""
    try:
        result = subprocess.run(['command', '-v', command], 
                              capture_output=True, 
                              text=True, 
                              shell=False)
        return result.returncode == 0
    except Exception:
        return False


def handle_restore_command(timestamp: str | None = None) -> None:
    """Handle the restore command logic.""" 
    try:
        restore_snapshot(timestamp)
        if timestamp:
            rprint(f"[green]All files restored to {timestamp}[/]")
        else:
            rprint("[green]All files restored to latest snapshot.[/]")
    except Exception as e:
        rprint(f"[red]Error restoring snapshot:[/] {e}")


def handle_history_command() -> None:
    """Handle the history command logic."""
    timestamps = list_snapshots()
    if not timestamps:
        rprint("[yellow]No snapshots found.[/]")
    else:
        rprint("[bold]Snapshot History:[/]")
        for ts in timestamps:
            rprint(f"  {ts}")


def handle_shell_command(command: str, args: list[str]) -> None:
    """Handle arbitrary shell commands by checking if they exist in the system."""
    if not _is_valid_command(command):
        rprint(f"[red]Error:[/] Command '{command}' is not found or not executable.")
        return
    
    try:
        cmd = [command] + args
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            rprint(result.stdout)
    except subprocess.CalledProcessError as e:
        rprint(f"[red]Error running {command} {' '.join(args)}:[/] {e.stderr}")
    except FileNotFoundError:
        rprint(f"[red]Error:[/] {command} is not installed or not found in PATH.")


def handle_diff_command(args: list[str]) -> None:
    """Handle the diff command logic according to specified cases."""
    if not args:
        rprint("[red]Error:[/] No file specified for diff.")
        return

    file_name = args[0]
    file_path = Path(file_name)
    if not file_path.exists():
        rprint(f"[red]Error:[/] File '{file_name}' does not exist.")
        return

    snapshots = list_snapshots(file_path)
    if not snapshots:
        rprint(f"[yellow]No snapshots found for file '{file_name}'.[/]")
        return

    snapshot_paths = {}
    for snap_ts, snap_path_str in snapshots:
        ordinal = snap_ts.split('_')[0]  # Extract ordinal like "001"
        full_ts = snap_ts.split('_')[1]  # Extract full timestamp like "20250916T214101"
        snapshot_paths[ordinal] = Path(snap_path_str)
        snapshot_paths[full_ts] = Path(snap_path_str)

    if len(args) == 1:
        # Case 3: Diff with most recent snapshot
        if snapshots:
            latest_snap_path = Path(snapshots[0][1])
            diff_files(file_path, latest_snap_path)
        else:
            rprint(f"[yellow]No snapshots available for '{file_name}'.[/]")

    elif len(args) == 2:
        # Case 1: Diff with specific snapshot ID
        snapshot_id = args[1]
        if snapshot_id in snapshot_paths:
            diff_files(file_path, snapshot_paths[snapshot_id])
        else:
            rprint(f"[red]Error:[/] Snapshot '{snapshot_id}' not found for file '{file_name}'.")

    elif len(args) == 3:
        # Case 2: Diff between two snapshots
        snap_id1 = args[1]
        snap_id2 = args[2]
        if snap_id1 not in snapshot_paths:
            rprint(f"[red]Error:[/] Snapshot '{snap_id1}' not found for file '{file_name}'.")
            return
        if snap_id2 not in snapshot_paths:
            rprint(f"[red]Error:[/] Snapshot '{snap_id2}' not found for file '{file_name}'.")
            return
        diff_files(snapshot_paths[snap_id1], snapshot_paths[snap_id2])

    else:
        rprint("[red]Error:[/] Too many arguments for diff command.")


def diff_files(file1: Path, file2: Path) -> None:
    """Show diff between two files using system diff command."""
    try:
        result = subprocess.run(
            ["diff", "--color=always", "-u", str(file2), str(file1)],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            clean_output = ANSI_RE.sub("", result.stdout)
            _diff_console.print(clean_output)
        else:
            rprint("[green]No differences found.[/]")
    except FileNotFoundError:
        rprint("[red]Error:[/] 'diff' command not found. Please install diffutils.")
    except Exception as e:
        rprint(f"[red]Error running diff:[/] {e}")


def filter_unchanged_files(updated_files: list) -> list:
    """Filter out files from updated_files list if their content hasn't changed compared to on-disk version."""
    changed_files = []
    for item in updated_files:
        file_path = Path(item["file_name"])
        new_content = item["file_content"]
        
        # If file doesn't exist on disk, consider it changed (new file)
        if not file_path.exists():
            changed_files.append(item)
            continue
            
        # Read current content and compare
        try:
            current_content = file_path.read_text()
            if current_content != new_content:
                changed_files.append(item)
        except Exception:
            # If we can't read the file, assume it should be updated
            changed_files.append(item)
            
    return changed_files


def process_chat_message(prompt: str, chat_id: Optional[int], root: Path, file_mask: str) -> Dict[str, any]:
    """Process a chat message and return the response."""
    source_files = collect_sources(root, file_mask)
    
    resp = cli_invoke(message=prompt, chat_id=chat_id or -1, source_files=source_files)
    
    assistant_resp_str = resp.get('assistant_response')
    assistant_resp = json.loads(assistant_resp_str)
    
    return {
        "response": resp,
        "assistant_response": assistant_resp,
        "new_chat_id": resp.get("chat_id"),
        "summary": assistant_resp.get("answer_summary"),
        "updated_files": assistant_resp.get("source_files", [])
    }

# Snapshot cleanup functions
def handle_prune_cmd(keep: int = 10) -> None:
    """Delete all but the most recent N snapshots."""
    from .snapshot import prune_snapshots
    try:
        deleted_count = prune_snapshots(keep)
        if deleted_count > 0:
            rprint(f"\u2705 {deleted_count} snapshots deleted. {keep} most recent snapshots kept.")
        else:
            rprint("\u2705 No snapshots deleted. You have fewer than the specified keep count.")
    except Exception as e:
        rprint(f"[red]Error pruning snapshots:[/] {e}")


def handle_cleanup_cmd(days: int = 30) -> None:
    """Delete snapshots older than N days."""
    from .snapshot import cleanup_snapshots
    try:
        deleted_count = cleanup_snapshots(days)
        if deleted_count > 0:
            rprint(f"\u2705 {deleted_count} snapshots older than {days} days deleted.")
        else:
            rprint(f"\u2705 No snapshots older than {days} days found.")
    except Exception as e:
        rprint(f"[red]Error cleaning up snapshots:[/] {e}")

# Configuration management functions
def handle_config_list() -> None:
    """List all configuration values."""
    config = list_config()
    if not config:
        rprint("[yellow]No configuration values set.[/]")
        return
    
    rprint("[bold]Current Configuration:[/]")
    for key, value in config.items():
        rprint(f"  {key}: {value}")


def handle_config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    # Try to parse value as JSON for proper typing
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        # If JSON parsing fails, keep as string
        parsed_value = value
    
    set_value(key, parsed_value)
    rprint(f"[green]Configuration '{key}' set to '{value}'.[/]")


def handle_config_get(key: str) -> None:
    """Get a configuration value."""
    value = get_value(key)
    if value is None:
        rprint(f"[yellow]Configuration key '{key}' not found.[/]")
    else:
        rprint(f"{key}: {value}")


def handle_config_delete(key: str) -> None:
    """Delete a configuration value."""
    if delete_value(key):
        rprint(f"[green]Configuration '{key}' deleted.[/]")
    else:
        rprint(f"[yellow]Configuration key '{key}' not found.[/]")
