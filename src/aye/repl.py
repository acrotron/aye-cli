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

from rich.console import Console

from .api import cli_invoke
from .snapshot import apply_updates
from .source_collector import collect_sources
from .command import handle_restore_command, handle_history_command, handle_shell_command, _is_valid_command, handle_diff_command
from .ui import (
    print_welcome_message,
    print_prompt,
    print_thinking_spinner,
    print_assistant_response,
    print_no_files_changed,
    print_files_updated,
    print_error
)


def filter_unchanged_files(updated_files: list) -> list:
    """Filter out files from updated_files list if their content hasn't changed compared to on-disk version."""
    changed_files = []
    for item in updated_files:
        file_path = Path(item["file_name"])
        new_content = item["file_content"]
        
        # If file doesn't exist on disk, consider it changed (new file)
        if not file_path.exists():
            changed_files.append(item)
            continue
            
        # Read current content and compare
        try:
            current_content = file_path.read_text()
            if current_content != new_content:
                changed_files.append(item)
        except Exception:
            # If we can't read the file, assume it should be updated
            changed_files.append(item)
            
    return changed_files


def chat_repl(conf) -> None:
    session = PromptSession(
        history=InMemoryHistory(),
        completer=CmdPathCompleter(),
        complete_style=CompleteStyle.READLINE_LIKE,   # “readline” style, no menu
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
                source_files = collect_sources(conf.root, conf.file_mask)

                for k in source_files.keys():
                    print(k)

                resp = cli_invoke(message=prompt, chat_id=chat_id or -1, source_files=source_files)
            
            # Extract and store new chat_id from response
            new_chat_id = resp.get("chat_id")
            if new_chat_id is not None:
                chat_id = new_chat_id
                chat_id_file.write_text(str(chat_id))
            
            assistant_resp_str = resp.get('assistant_response')
            assistant_resp = json.loads(assistant_resp_str)

            summary = assistant_resp.get("answer_summary")
            print_assistant_response(summary)

            updated_files = assistant_resp.get("source_files", [])
            
            # Filter unchanged files
            updated_files = filter_unchanged_files(updated_files)
            
            if not updated_files:
                print_no_files_changed(console)
            elif updated_files:
                batch_ts = apply_updates(updated_files)
                file_names = [item.get("file_name") for item in updated_files if "file_name" in item]
                if file_names:
                    print_files_updated(console, file_names)
            rprint()
        except Exception as exc:
            print_error(exc)
            continue
