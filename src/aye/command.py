import subprocess
from .snapshot import restore_snapshot, list_snapshots
from rich import print as rprint

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

def handle_git_diff_command(file_name: str | None = None) -> None:
    """Handle the git diff command logic."""
    try:
        cmd = ["git", "diff"]
        if file_name:
            cmd.append(file_name)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            rprint(result.stdout)
        else:
            rprint("[yellow]No differences found.[/]")
    except subprocess.CalledProcessError as e:
        rprint(f"[red]Error running git diff:[/] {e.stderr}")