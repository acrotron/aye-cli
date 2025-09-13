from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich import print as rprint

from .api import cli_invoke
from .snapshot import create_snapshot
from .source_collector import collect_sources


def chat_repl(file: Optional[Path] = None) -> None:
    session = PromptSession(history=InMemoryHistory())
    rprint("[bold cyan]Aye CLI – type /exit or Ctrl‑D to quit[/]")

    while True:
        try:
            #prompt = session.prompt("🧠 » ")
            #prompt = session.prompt("(ツ) » ")
            #prompt = session.prompt("◉ ‿ ◉ » ")
            #prompt = session.prompt("(•̀ᴗ•́) » ")
            #prompt = session.prompt("{•!•} » ")
            #prompt = session.prompt("{•I•} » ")
            #prompt = session.prompt("(⊙_⊙) » ")
            #prompt = session.prompt("{•_・} » ")
            #prompt = session.prompt("{olO} » ")
            #prompt = session.prompt("{•_•} » ")
            prompt = session.prompt("-{•_•}- » ")
            #prompt = session.prompt("{o_o} » ")
            #prompt = session.prompt("{⌐■_■} » ")
        except (EOFError, KeyboardInterrupt):
            break

        if prompt.strip() in {"/exit", "/quit"}:
            break

        # Call the backend
        try:
            #resp = generate(prompt, filename=str(file) if file else None)
            #code = resp.get("generated_code", "")
            folder = "aye"
            source_files = collect_sources(folder)
            resp = cli_invoke(message=prompt, chat_id=181, source_files=source_files) 
            #rprint(f"[green] {resp.get('assistant_response')}")
            rprint(f"[gray] {resp.get('assistant_response')}")
        except Exception as exc:
            rprint(f"[red]Error:[/] {exc}")
            continue

        #if file:
        #    # Undo point before we overwrite the file
        #    create_snapshot(file)
        #    file.write_text(code)
        #    rprint(f"[green]✔[/] Updated {file}")
        #else:
        #    rprint("[yellow]--- generated code ---[/]")
        #    rprint(code)
        #    rprint("[yellow]----------------------[/]")

