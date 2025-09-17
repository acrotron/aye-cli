import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import PathCompleter
from .completers import CmdPathCompleter
from prompt_toolkit.shortcuts import CompleteStyle

from rich import print as rprint
from rich.text import Text
from rich.padding import Padding
from rich.console import Console
from rich.spinner import Spinner

from .api import cli_invoke
from .snapshot import apply_updates
from .source_collector import collect_sources
from .command import handle_restore_command, handle_history_command, handle_shell_command, _is_valid_command, handle_diff_command


def chat_repl(conf) -> None:
    session = PromptSession(
        history=InMemoryHistory(),
        completer=CmdPathCompleter(),
        complete_style=CompleteStyle.READLINE_LIKE,   # “readline” style, no menu
        complete_while_typing=False)

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

        if not prompt.strip():
            continue

        # Tokenize input to check for commands
        tokens = prompt.strip().split()
        first_token = tokens[0].lower()

        # Check for exit commands
        if first_token in {"/exit", "/quit", "exit", "quit", ":q", "/q"}:
            break

        # Check for history commands
        if first_token in {"/history", "history"}:
            handle_history_command()
            continue

        # Check for restore commands
        if first_token in {"/restore", "restore"}:
            handle_restore_command(None)
            continue

        # Check for diff commands
        if first_token in {"/diff", "diff"}:
            handle_diff_command(tokens[1:])
            continue

        # Handle shell commands with or without forward slash
        command = first_token.lstrip('/')
        if _is_valid_command(command):
            args = tokens[1:]
            handle_shell_command(command, args)
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
