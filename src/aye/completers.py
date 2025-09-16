# completers.py
from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.document import Document


class CmdPathCompleter(Completer):
    """
    Completes:
    • the first token with an optional list of commands
    • the *last* token (any argument) as a filesystem path
    """

    def __init__(self, commands: list[str] | None = None):
        self.commands = commands or []
        self._path_completer = PathCompleter()

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        words = text.split()

        # ----- 1️⃣  First word → command completions (optional) -----
        if len(words) == 0:
            return
        if len(words) == 1 and not text.endswith(" "):
            # Still typing the command itself
            prefix = words[0]
            for cmd in self.commands:
                if cmd.startswith(prefix):
                    yield Completion(
                        cmd,
                        start_position=-len(prefix),
                        display=cmd,
                    )
            return

        # ----- 2️⃣  Anything after a space → path completion -----
        # The word we are currently completing (the part after the last space)
        last_word = words[-1]

        # Create a temporary Document that contains only that word.
        sub_doc = Document(text=last_word, cursor_position=len(last_word))

        for comp in self._path_completer.get_completions(sub_doc, complete_event):
            # Forward the inner completion unchanged – its start_position is
            # already the negative length of `last_word`.
            yield Completion(
                comp.text,
                start_position=comp.start_position,
                display=comp.display,
            )

