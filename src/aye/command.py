import subprocess
import re
from rich import print as rprint
from pathlib import Path
from rich.console import Console
from .snapshot import restore_snapshot, list_snapshots


import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mK]")


# Create a global console instance for diff output
_diff_console = Console(force_terminal=True, markup=False, color_system="standard")

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


