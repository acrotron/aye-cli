from pathlib import Path
import typer

from .service import (
    handle_login,
    handle_logout,
    handle_generate_cmd,
    handle_chat,
    handle_history_cmd,
    handle_snap_show_cmd,
    handle_restore_cmd,
    handle_prune_cmd,
    handle_cleanup_cmd,
    handle_config_list,
    handle_config_set,
    handle_config_get,
    handle_config_delete
)

from .config import load_config

# Load configuration at startup
load_config()

app = typer.Typer(help="Aye: AI‑powered coding assistant for the terminal")

# ----------------------------------------------------------------------
# Authentication commands
# ----------------------------------------------------------------------
@app.command()
def login(
    url: str = typer.Option(
        "https://auth.example.com/cli-login",
        "--url",
        help="Login page that returns a one‑time token",
    )
):
    """
    Configure username and token for authenticating with the aye service.
    
    Examples:
    aye login
    aye login --url https://my-auth-service.com/login
    """
    handle_login(url)


@app.command()
def logout():
    """
    Remove the stored aye credentials.
    
    Examples:
    aye logout
    """
    handle_logout()

# ----------------------------------------------------------------------
# One‑shot generation
# ----------------------------------------------------------------------
@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Prompt for the LLM"),
    file: Path = typer.Option(
        None, "--file", "-f", help="Path to the file to be modified"
    ),
    mode: str = typer.Option(
        "replace",
        "--mode",
        "-m",
        help="replace | append | insert (default: replace)",
    ),
):
    """
    Send a single prompt to the backend.  If `--file` is supplied,
    the file is snapshotted first, then overwritten/appended.
    
    Examples:
    aye generate "Create a function that reverses a string"
    aye generate "Add type hints to this function" --file src/utils.py
    aye generate "Add a docstring to this class" --file src/models.py --mode append
    """
    handle_generate_cmd(prompt, file, mode)

# ----------------------------------------------------------------------
# Interactive REPL (chat) command
# ----------------------------------------------------------------------
@app.command()
def chat(
    root: Path = typer.Option(
        None, "--root", "-r", help="Root folder where source files are located."
    ),
    file_mask: str = typer.Option(
        "*.py", "--file-mask", "-m", help="File mask for source files to include into generation."
    ),
):
    """
    Start an interactive REPL. Use /exit or Ctrl‑D to leave.
    
    Examples:
    aye chat
    aye chat --root ./src
    aye chat --file-mask "*.js" --root ./frontend
    """
    handle_chat(root, file_mask)

# ----------------------------------------------------------------------
# Snapshot commands (moved from snap subcommand)
# ----------------------------------------------------------------------
@app.command("history")
def history_cmd(
    file: Path = typer.Argument(None, help="File to list snapshots for")
):
    """
    Show timestamps of saved snapshots for *file* or all snapshots if no file provided.
    
    Examples:
    aye history
    aye history src/main.py
    """
    handle_history_cmd(file)


@app.command("show")
def snap_show_cmd(
    file: Path = typer.Argument(..., help="File whose snapshot to show"),
    ts: str = typer.Argument(..., help="Timestamp of the snapshot"),
):
    """
    Print the contents of a specific snapshot.
    
    Examples:
    aye show src/main.py 001_20250916T214101
    aye show src/main.py 001
    """
    handle_snap_show_cmd(file, ts)


@app.command("restore")
def restore_cmd(
    ts: str = typer.Argument(None, help="Timestamp of the snapshot to restore (default: latest)"),
):
    """
    Replace all files with the latest snapshot or specified snapshot.
    
    Examples:
    aye restore
    aye restore 001_20250916T214101
    aye restore 001
    """
    handle_restore_cmd(ts)


# ----------------------------------------------------------------------
# Snapshot cleanup/pruning commands
# ----------------------------------------------------------------------
@app.command()
def prune(
    keep: int = typer.Option(10, "--keep", "-k", help="Number of recent snapshots to keep (default: 10)"),
):
    """
    Delete all but the most recent N snapshots.
    
    Examples:
    aye prune
    aye prune --keep 5
    aye prune -k 3
    """
    handle_prune_cmd(keep)


@app.command()
def cleanup(
    days: int = typer.Option(30, "--days", "-d", help="Delete snapshots older than N days (default: 30)"),
):
    """
    Delete snapshots older than N days.
    
    Examples:
    aye cleanup
    aye cleanup --days 7
    aye cleanup -d 14
    """
    handle_cleanup_cmd(days)


# ----------------------------------------------------------------------
# Configuration management commands
# ----------------------------------------------------------------------
@app.command()
def config(
    action: str = typer.Argument(..., help="Action to perform: list, get, set, delete"),
    key: str = typer.Argument(None, help="Configuration key"),
    value: str = typer.Argument(None, help="Configuration value (for set action)"),
):
    """
    Manage configuration values for file masks, root directories, and other settings.
    
    Actions:
    - list: Show all configuration values
    - get: Retrieve a specific configuration value
    - set: Set a configuration value
    - delete: Remove a configuration value
    
    Examples:
    aye config list
    aye config get file_mask
    aye config set file_mask "*.py,*.js"
    aye config delete file_mask
    """
    if action == "list":
        handle_config_list()
    elif action == "get":
        if not key:
            print("[red]Error:[/] Key is required for get action.")
            raise typer.Exit(code=1)
        handle_config_get(key)
    elif action == "set":
        if not key or not value:
            print("[red]Error:[/] Key and value are required for set action.")
            raise typer.Exit(code=1)
        handle_config_set(key, value)
    elif action == "delete":
        if not key:
            print("[red]Error:[/] Key is required for delete action.")
            raise typer.Exit(code=1)
        handle_config_delete(key)
    else:
        print(f"[red]Error:[/] Invalid action '{action}'. Use: list, get, set, delete")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
