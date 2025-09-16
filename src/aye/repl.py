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
from .snapshot import apply_updates
from .source_collector import collect_sources


def chat_repl(conf) -> None:
    session = PromptSession(history=InMemoryHistory())
    rprint("[bold cyan]Aye CLI – type /exit or Ctrl‑D to quit[/]")

    while True:
        try:
            prompt = session.prompt("(ツ) » ")
        except (EOFError, KeyboardInterrupt):
            break

        if prompt.strip() in {"/exit", "/quit"}:
            break

        # Call the backend
        try:
            source_files = collect_sources(conf.root, conf.file_mask)
            resp = cli_invoke(message=prompt, chat_id=-1, source_files=source_files)
            assistant_resp_str = resp.get('assistant_response')
            assistant_resp = json.loads(assistant_resp_str)

            # Update files with snapshots
            updated_files = assistant_resp.get("source_files", [])
            if updated_files:
                batch_ts = apply_updates(updated_files) # snapshot + write
                rprint(f"[green]✅ Batch snapshot created: {batch_ts}[/]")

            summary = assistant_resp.get("answer_summary")
            console = Console()
            rprint()
            color = "rgb(170,170,170)"
            rprint(f"[{color}]    -{{•!•}}- »[/]")
            console.print(Padding(summary, (0, 4, 0, 4)), style=color)
            rprint()
        except Exception as exc:
            rprint(f"[red]Error:[/] {exc}")
            continue


