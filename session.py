import json
from datetime import datetime
from pathlib import Path


SESSION_DIR = Path.cwd() / ".agents" / "sessions"
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
WRITTEN = 0


def path_for(session_id):
    return SESSION_DIR / f"{session_id}.jsonl"


def save(messages):
    """Append new messages to the current transcript."""
    global WRITTEN
    if len(messages) == WRITTEN:
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as file:
        for message in messages[WRITTEN:]:
            file.write(json.dumps(message, ensure_ascii=False) + "\n")
    WRITTEN = len(messages)


def rewind_to(count):
    """Record a rewind without deleting the original transcript entries."""
    global WRITTEN
    with path_for(CURRENT).open("a", encoding="utf-8") as file:
        file.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = count


def load(session_id):
    messages = []
    for line in path_for(session_id).read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
        else:
            messages.append(entry)
    return messages


def open_session(session_id):
    global CURRENT, WRITTEN
    messages = load(session_id)
    CURRENT = session_id
    WRITTEN = len(messages)
    return messages


def title(messages):
    for message in messages:
        if message["role"] == "user":
            return " ".join(str(message.get("content") or "").split())[:60]
    return "(empty)"


def all_sessions():
    files = sorted(
        SESSION_DIR.glob("*.jsonl"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    return [{"id": path.stem, "title": title(load(path.stem))} for path in files]
