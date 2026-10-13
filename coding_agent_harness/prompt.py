from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style


HISTORY = Path.cwd() / ".agents" / "history"
SESSION = None
BINDINGS = KeyBindings()
STYLE = Style.from_dict({"prompt": "bold #9ece6a"})


@BINDINGS.add("escape", "left")
def word_left(event):
    buffer = event.current_buffer
    buffer.cursor_position += buffer.document.find_previous_word_beginning() or 0


@BINDINGS.add("escape", "right")
def word_right(event):
    buffer = event.current_buffer
    buffer.cursor_position += buffer.document.find_next_word_ending() or 0


@BINDINGS.add("escape", "enter")
def newline(event):
    event.current_buffer.insert_text("\n")


def read(label="> "):
    global SESSION
    if SESSION is None:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        SESSION = PromptSession(
            history=FileHistory(str(HISTORY)),
            key_bindings=BINDINGS,
            style=STYLE,
        )
    return SESSION.prompt(FormattedText([("class:prompt", label)]))
