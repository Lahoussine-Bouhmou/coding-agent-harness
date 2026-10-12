import session


COMMANDS = {
    "/rewind": "return to an earlier completed turn (conversation only)",
    "/sessions": "open a saved conversation",
}


def preview(message):
    return " ".join(str(message.get("content") or "").split())[:70]


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
    ui.note("Conversation rewound. Files and executed commands are unchanged.")
    return messages[:count]


def sessions(messages, ui):
    saved = session.all_sessions()
    if not saved:
        ui.note("No saved conversations yet.")
        return messages
    choice = ui.pick("Open conversation", [f"{s['id']}  {s['title']}" for s in saved])
    if choice is None:
        return messages
    messages = session.open_session(saved[choice]["id"])
    ui.resumed(messages)
    return messages


def handle(command, messages, ui):
    if command == "/rewind":
        return rewind(messages, ui)
    if command == "/sessions":
        return sessions(messages, ui)
    ui.note("\n".join(f"{name}  -  {description}" for name, description in COMMANDS.items()))
    return messages
