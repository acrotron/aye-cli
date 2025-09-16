import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich import print as rprint
from rich.text import Text
from rich.padding import Padding
from rich.console import Console
from rich.spinner import Spinner

from .api import cli_invoke
from .snapshot import apply_updates
from .source_collector import collect_sources
from .command import handle_restore_command, handle_history_command, handle_git_diff_command


def chat_repl(conf) -> None:
    session = PromptSession(history=InMemoryHistory())
    rprint("[bold cyan]Aye CLI – type /exit or Ctrl‑D to quit[/]")
    console = Console()

    # Path to store chat_id persistently during session
    chat_id_file = Path(".aye/chat_id.tmp")
    chat_id = None

    # Load chat_id if exists from previous session
    if chat_id_file.exists():
        try:
            chat_id = int(chat_id_file.read_text().strip())
        except ValueError:
            chat_id_file.unlink(missing_ok=True)  # Clear invalid file

    while True:
        try:
            prompt = session.prompt("(ツ » ")
        except (EOFError, KeyboardInterrupt):
            break

        if prompt.strip() in {"/exit", "/quit", "exit", "quit"}:
            break

        if prompt.strip() in {"/history", "history"}:
            handle_history_command()
            continue

        if prompt.strip() in {"/restore", "restore"}:
            handle_restore_command(None)
            continue

        if prompt.strip() in {"/git status", "git status"}:
            try:
                result = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
                rprint(result.stdout)
            except subprocess.CalledProcessError as e:
                rprint(f"[red]Error running git status:[/] {e.stderr}")
            continue

        if prompt.strip().startswith(('/git diff', 'git diff')):
            parts = prompt.strip().split()
            file_name = parts[2] if len(parts) > 2 else None
            handle_git_diff_command(file_name)
            continue

        if not prompt.strip():
            continue

        spinner = Spinner("dots", text="[yellow]Thinking...[/]")
        
        try:
            with console.status(spinner) as status:
                source_files = collect_sources(conf.root, conf.file_mask)
                resp = cli_invoke(message=prompt, chat_id=chat_id or -1, source_files=source_files)
            
            # Extract and store new chat_id from response
            new_chat_id = resp.get("chat_id")
            if new_chat_id is not None:
                chat_id = new_chat_id
                chat_id_file.write_text(str(chat_id))
            
            assistant_resp_str = resp.get('assistant_response')
            assistant_resp = json.loads(assistant_resp_str)

            summary = assistant_resp.get("answer_summary")
            rprint()
            color = "rgb(170,170,170)"
            rprint(f"[{color}]    -{{•!•}}- »[/]")
            console.print(Padding(summary, (0, 4, 0, 4)), style=color)
            rprint()

            updated_files = assistant_resp.get("source_files", [])
            if updated_files:
                batch_ts = apply_updates(updated_files)
                file_names = [item.get("file_name") for item in updated_files if "file_name" in item]
                if file_names:
                    console.print(Padding(f"[green]Files updated:[/] {','.join(file_names)}", (0, 4, 0, 4)))
        except Exception as exc:
            rprint(f"[red]Error:[/] {exc}")
            continue
