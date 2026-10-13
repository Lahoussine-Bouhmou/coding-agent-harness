from . import session
from . import sandbox
from . import compact as compaction
from . import history


COMMANDS = {
    "/rewind": "return to an earlier completed turn (conversation only)",
    "/sessions": "open a saved conversation",
    "/compact": "summarize older history to free context space",
}


def preview(message):
    return " ".join(str(message.get("content") or "").split())[:70]


def redraw(messages, ui, label):
    ui.clear()
    ui.banner(sandbox.name())
    ui.resumed(messages, label)
    ui.replay(messages)
    return messages


def rewind(messages, ui):
    # Keep tool requests together with all their results.
    points = [
        index + 1 for index, message in enumerate(messages)
        if message["role"] == "system"
        or (message["role"] == "assistant" and not message.get("tool_calls"))
    ]
    rows = [
        f"{messages[count - 1]['role']:<9} {preview(messages[count - 1])}"
        for count in points
    ]
    choice = ui.pick("Rewind to", rows)
    if choice is None:
        return messages
    count = points[choice]
    session.save(messages)
    session.rewind_to(count)
    messages = redraw(messages[:count], ui, "Rewound")
    ui.note("Conversation rewound. Files and executed commands are unchanged.")
    return messages


def sessions(messages, ui):
    saved = session.all_sessions()
    if not saved:
        ui.note("No saved conversations yet.")
        return messages
    choice = ui.pick("Open conversation", [f"{s['id']}  {s['title']}" for s in saved])
    if choice is None:
        return messages
    messages = session.open_session(saved[choice]["id"])
    history.strip(messages)
    return redraw(messages, ui, "Opened")


def compact(messages, ui):
    try:
        with ui.working("Compacting conversation…"):
            compacted = compaction.compact(messages)
    except Exception as error:
        ui.note(f"Compaction failed ({type(error).__name__}); conversation history kept.")
        return messages
    if compacted is messages:
        ui.note("Nothing old enough to compact yet.")
        return messages
    session.save(messages)
    session.compacted(compacted)
    ui.compacted(len(messages), compacted)
    return compacted


def handle(command, messages, ui):
    if command == "/compact":
        return compact(messages, ui)
    if command == "/rewind":
        return rewind(messages, ui)
    if command == "/sessions":
        return sessions(messages, ui)
    ui.note("\n".join(f"{name}  -  {description}" for name, description in COMMANDS.items()))
    return messages
