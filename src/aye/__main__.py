from pathlib import Path
import typer

from .auth import login_flow, delete_token
from .repl import chat_repl
from .api import generate
from .snapshot import (
    create_snapshot,
    list_snapshots,
    restore_snapshot,
)

app = typer.Typer(help="Aye – AI‑Zap terminal assistant with snapshot/undo")

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
    """Open a browser, obtain a token, and store it locally."""
    login_flow(url)


@app.command()
def logout():
    """Remove the stored auth token."""
    delete_token()
    typer.secho("🔐 Token removed.", fg=typer.colors.GREEN)

# ----------------------------------------------------------------------
# One‑shot generation
# ----------------------------------------------------------------------
@app.command()
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

    resp = generate(prompt, filename=str(file) if file else None, mode=mode)
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
    file: Path = typer.Option(
        None, "--file", "-f", help="File to edit while chatting"
    )
):
    """Start an interactive REPL. Use /exit or Ctrl‑D to leave."""
    chat_repl(file)

# ----------------------------------------------------------------------
# Snapshot / undo sub‑commands
# ----------------------------------------------------------------------
snap = typer.Typer(help="Snapshot / undo utilities")
app.add_typer(snap, name="snap")


@snap.command("list")
def snap_list(
    file: Path = typer.Argument(..., help="File to list snapshots for")
):
    """Show timestamps of saved snapshots for *file*."""
    snaps = list_snapshots(file)
    if not snaps:
        typer.echo("No snapshots found.")
        raise typer.Exit()
    for ts, _ in snaps:
        typer.echo(ts)


@snap.command("show")
def snap_show(
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


@snap.command("revert")
def snap_revert(
    file: Path = typer.Argument(..., help="File to revert"),
    ts: str = typer.Argument(..., help="Timestamp of the snapshot to restore"),
):
    """Replace the current file with a previous snapshot."""
    try:
        restore_snapshot(file, ts)
        typer.secho(f"✅ {file} restored to {ts}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()


