from pathlib import Path
import typer
from types import SimpleNamespace

from .auth import login_flow, delete_token
from .repl import chat_repl
from .api import cli_invoke
from .snapshot import (
    create_snapshot,
    list_snapshots,
    restore_snapshot,
)

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
    """Configure username and token for authenticating with the aye service."""
    login_flow(url)


@app.command()
def logout():
    """Remove the stored aye credentials."""
    delete_token()
    typer.secho("🔐 Token removed.", fg=typer.colors.GREEN)

# ----------------------------------------------------------------------
# One‑shot generation
# ----------------------------------------------------------------------
#@app.command()
def generate_cmd(
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
    """
    if file:
        create_snapshot(file)          # ← undo point

    resp = cli_invoke(prompt, filename=str(file) if file else None, mode=mode)
    code = resp.get("generated_code", "")

    if file:
        file.write_text(code)
        typer.secho(f"✅ {file} updated (snapshot taken)", fg=typer.colors.GREEN)
    else:
        typer.echo(code)

# ----------------------------------------------------------------------
# Interactive REPL (chat) command
# ----------------------------------------------------------------------
@app.command()
def chat(
    root: Path = typer.Option(
        ".", "--root", "-r", help="Root folder where source files are located."
    ),
    file_mask: str = typer.Option(
        "*.py", "--file-mask", "-m", help="File mask for source files to include into generation."
    ),
    #file: Path = typer.Option(
    #    None, "--file", "-f", help="File to edit while chatting"
    #)
):
    """Start an interactive REPL. Use /exit or Ctrl‑D to leave."""
    conf = SimpleNamespace()
    conf.root = root
    conf.file_mask = file_mask
    chat_repl(conf)

# ----------------------------------------------------------------------
# Snapshot commands (moved from snap subcommand)
# ----------------------------------------------------------------------
@app.command("history")
def history_cmd(
    file: Path = typer.Argument(None, help="File to list snapshots for")
):
    """Show timestamps of saved snapshots for *file* or all snapshots if no file provided."""
    if file is None:
        # List all snapshots in descending order with file names
        timestamps = list_snapshots()
        if not timestamps:
            typer.echo("No snapshots found.")
            raise typer.Exit()
        for ts in timestamps:
            # Read metadata to get file list
            meta_path = Path(".aye/snapshots/batches") / ts / "metadata.json"
            if meta_path.exists():
                import json
                meta = json.loads(meta_path.read_text())
                files = [Path(entry["original"]).name for entry in meta["files"]]
                files_str = ",".join(files)
                typer.echo(f"{ts}  {files_str}")
            else:
                typer.echo(f"{ts}  (metadata missing)")
    else:
        # Original behavior for specific file
        snaps = list_snapshots(file)
        if not snaps:
            typer.echo("No snapshots found.")
            raise typer.Exit()
        for ts, _ in snaps:
            typer.echo(ts)


@app.command("show")
def snap_show_cmd(
    file: Path = typer.Argument(..., help="File whose snapshot to show"),
    ts: str = typer.Argument(..., help="Timestamp of the snapshot"),
):
    """Print the contents of a specific snapshot."""
    for snap_ts, snap_path in list_snapshots(file):
        if snap_ts == ts:
            typer.echo(Path(snap_path).read_text())
            raise typer.Exit()
    typer.echo("Snapshot not found.", err=True)
    raise typer.Exit(code=1)


@app.command("restore")
def restore_cmd(
    ts: str = typer.Argument(None, help="Timestamp of the snapshot to restore (default: latest)"),
):
    """Replace all files with the latest snapshot or specified snapshot."""
    try:
        restore_snapshot(ts)
        if ts:
            typer.secho(f"✅ All files restored to {ts}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"✅ All files restored to latest snapshot", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
