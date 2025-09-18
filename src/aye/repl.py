import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import PathCompleter
from .completers import CmdPathCompleter
from prompt_toolkit.shortcuts import CompleteStyle

from rich.console import Console

from .service import (
    _is_valid_command,
    handle_restore_command,
    handle_history_command,
    handle_shell_command,
    handle_diff_command,
    process_chat_message,
    filter_unchanged_files
)

from .ui import (
    print_welcome_message,
    print_prompt,
    print_thinking_spinner,
    print_assistant_response,
    print_no_files_changed,
    print_files_updated,
    print_error 
)

from .snapshot import apply_updates


def chat_repl(conf) -> None:
    session = PromptSession(
        history=InMemoryHistory(),
        completer=CmdPathCompleter(),
        complete_style=CompleteStyle.READLINE_LIKE,   # "readline" style, no menu
        complete_while_typing=False)

    print_welcome_message()
    console = Console()

    # Path to store chat_id persistently during session
    chat_id_file = Path(".aye/chat_id.tmp")
    chat_id_file.parent.mkdir(parents=True, exist_ok=True)
    chat_id = None

    # Load chat_id if exists from previous session
    if chat_id_file.exists():
        try:
            chat_id = int(chat_id_file.read_text().strip())
        except ValueError:
            chat_id_file.unlink(missing_ok=True)  # Clear invalid file

    while True:
        try:
            prompt = session.prompt(print_prompt())
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
        if first_token in {"/restore", "/revert", "restore", "revert"}:
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

        spinner = print_thinking_spinner(console)
        
        try:
            with console.status(spinner) as status:
                result = process_chat_message(prompt, chat_id, conf.root, conf.file_mask)
            
            # Extract and store new chat_id from response
            new_chat_id = result["new_chat_id"]
            if new_chat_id is not None:
                chat_id = new_chat_id
                chat_id_file.write_text(str(chat_id))
            
            summary = result["summary"]
            print_assistant_response(summary)

            updated_files = result["updated_files"]
            
            # Filter unchanged files
            updated_files = filter_unchanged_files(updated_files)
            
            if not updated_files:
                print_no_files_changed(console)
            elif updated_files:
                batch_ts = apply_updates(updated_files)
                file_names = [item.get("file_name") for item in updated_files if "file_name" in item]
                if file_names:
                    print_files_updated(console, file_names)
        except Exception as exc:
            print_error(exc)
            continue
