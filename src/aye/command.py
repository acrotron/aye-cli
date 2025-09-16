import subprocess
from .snapshot import restore_snapshot, list_snapshots
from rich import print as rprint


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
            print(f"[green]✅ All files restored to {timestamp}[/]")
        else:
            print("[green]✅ All files restored to latest snapshot.[/]")
    except Exception as e:
        print(f"[red]Error restoring snapshot:[/] {e}")


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
