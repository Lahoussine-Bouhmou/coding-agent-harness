import subprocess
from datetime import datetime
from pathlib import Path


SEEN = {}


def note_read(path):
    """Remember the modification time of a file read by the agent."""
    path = Path(path).resolve()
    SEEN[str(path)] = path.stat().st_mtime_ns


def stale_files():
    changed = []
    for path, mtime in SEEN.items():
        try:
            current_mtime = Path(path).stat().st_mtime_ns
        except OSError:
            changed.append(path)
            continue
        if current_mtime != mtime:
            changed.append(path)
    return changed


def stale_note():
    changed = stale_files()
    if not changed:
        return ""
    return (
        "\n<system-reminder>\n"
        "These files changed or became unavailable since you read them. "
        "Read them again before editing:\n"
        + "\n".join(changed)
        + "\n</system-reminder>"
    )


def git_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "(not a git repository)"
    return result.stdout.strip() or "(detached)"


def reminder():
    """Build fresh environment context for the end of a model request."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now().astimezone():%Y-%m-%d %H:%M %z}\n"
            f"git branch: {git_branch()}\n"
            "</env>" + stale_note()
        ),
    }
