import os, sys
import json
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich import print as rprint
from rich.text import Text
from rich.padding import Padding
from rich.console import Console

from .api import cli_invoke
from .snapshot import create_snapshot
from .source_collector import collect_sources


def chat_repl(conf) -> None:
    session = PromptSession(history=InMemoryHistory())
    rprint("[bold cyan]Aye CLI – type /exit or Ctrl‑D to quit[/]")

    while True:
        try:
            prompt = session.prompt("(ツ) » ")
            #prompt = session.prompt("◉ ‿ ◉ » ")
            #prompt = session.prompt("(•̀ᴗ•́) » ")
            #prompt = session.prompt("{•!•} » ")
            #prompt = session.prompt("{•I•} » ")
            #prompt = session.prompt("(⊙_⊙) » ")
            #prompt = session.prompt("{•_・} » ")
            #prompt = session.prompt("{olO} » ")
            #prompt = session.prompt("{•_•} » ")
            #prompt = session.prompt("-{•!•}- » ")
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
            source_files = collect_sources(conf.root, conf.file_mask)
            resp = cli_invoke(message=prompt, chat_id=-1, source_files=source_files)
            assistant_resp_str = resp.get('assistant_response')
            assistant_resp = json.loads(assistant_resp_str)
            summary = assistant_resp.get("answer_summary")
            updated_files = [f["file_name"] for f in assistant_resp["source_files"]]

            console = Console()
            #summary = assistant_resp.get("answer_summary") if assistant_resp else "Unclear"
            #rprint(f"[green] {resp.get('assistant_response')}")
            rprint()
            color = "rgb(170,170,170)"
            #rprint(f"[{color}]----------------------[/]")
            rprint(f"[{color}]    -{{•!•}}- »[/]")
            console.print(Padding(summary, (0,4,0,4)), style=color)
            #rprint(Text(summary, style="green").pad(8))
            #rprint()
            console.print(Padding(f"Updated files: {updated_files}", (0,4,0,4)), style=color)
            #rprint(f"[{color}]----------------------[/]")
            rprint()
            ##rprint(f"{resp.get('assistant_response')}")
            #for k, v in assistant_resp.items():
            #    rprint(f"[brown] {k}: {v}[/]")
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

