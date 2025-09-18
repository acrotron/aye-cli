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
    process_repl_message
)

from .ui import (
    print_welcome_message,
    print_prompt,
    print_thinking_spinner
)


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
        
        # Process the message using the new service function
        process_repl_message(prompt, chat_id, conf.root, conf.file_mask, chat_id_file, console)
