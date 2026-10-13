import json
import tempfile
from pathlib import Path

from . import config


CAP = 10_000
STUB = 300
CAPPED = "[output capped:"
TRIMMED = "[output trimmed:"
SUMMARY = "<summary>"
SPILLS = []


def cap(text):
    if len(text) <= CAP:
        return text
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix="harness-output-", suffix=".txt", delete=False
    ) as file:
        file.write(text)
        path = Path(file.name)
    SPILLS.append(path)
    return (
        text[:CAP]
        + f"\n\n{CAPPED} {len(text) - CAP} characters omitted. "
        f"Full output: {path}. Read sections with head, tail, sed, or grep. "
        "This file is deleted when the current turn ends.]"
    )


def sweep():
    for path in SPILLS:
        path.unlink(missing_ok=True)
    SPILLS.clear()


def locked(messages):
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if message["role"] == "user" and (message.get("content") or "").startswith(SUMMARY):
            return index + 1
    return 0


def strip(messages):
    shrunk = 0
    for message in messages[locked(messages):]:
        content = message.get("content") or ""
        if message["role"] != "tool" or TRIMMED in content or len(content) <= STUB:
            continue
        message["content"] = (
            content[:STUB]
            + f"\n\n{TRIMMED} older output omitted. Read the file or run the command again if needed.]"
        )
        shrunk += 1
    return shrunk


def estimate(messages):
    """Approximate token count; provider usage remains the authoritative count."""
    return sum(len(json.dumps(message)) for message in messages) // 4


def fit(messages, extra=None):
    budget = config.CONTEXT_WINDOW * config.COMPACT_AT
    dropped = 0
    for message in messages[locked(messages):]:
        if estimate(messages + (extra or [])) <= budget:
            break
        if message["role"] == "tool" and not (message.get("content") or "").startswith(TRIMMED):
            message["content"] = f"{TRIMMED} dropped to fit the context window.]"
            dropped += 1
    return dropped
