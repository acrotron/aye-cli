from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich import print as rprint

from .api import generate
from .snapshot import create_snapshot


def chat_repl(file: Optional[Path] = None) -> None:
    session = PromptSession(history=InMemoryHistory())
    rprint("[bold cyan]Aye REPL – type /exit or Ctrl‑D to quit[/]")

    while True:
        try:
            prompt = session.prompt("🧠 » ")
        except (EOFError, KeyboardInterrupt):
            break

        if prompt.strip() in {"/exit", "/quit"}:
            break

        # Call the backend
        try:
            resp = generate(prompt, filename=str(file) if file else None)
            code = resp.get("generated_code", "")
        except Exception as exc:
            rprint(f"[red]Error:[/] {exc}")
            continue

        if file:
            # Undo point before we overwrite the file
            create_snapshot(file)
            file.write_text(code)
            rprint(f"[green]✔[/] Updated {file}")
        else:
            rprint("[yellow]--- generated code ---[/]")
            rprint(code)
            rprint("[yellow]----------------------[/]")

