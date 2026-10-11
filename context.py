import subprocess
from datetime import datetime


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
            "</env>"
        ),
    }
