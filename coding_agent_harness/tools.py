import subprocess

from .context import note_read
from .skills import read_skill


def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=60
    )
    return (result.stdout + result.stderr) or "(no output)"


def read_file(path: str) -> str:
    """Read a text file and return its contents."""
    with open(path, encoding="utf-8") as file:
        content = file.read()
    note_read(path)
    return content


def write_file(path: str, content: str) -> str:
    """Create a text file or overwrite its existing contents."""
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    return f"Wrote {path}"


def str_replace(
    path: str, old_str: str, new_str: str, allow_multi_edit: bool = False
) -> str:
    """Replace exact text, requiring a unique match unless explicitly allowed."""
    if not old_str:
        return "Error: old_str must not be empty"
    content = read_file(path)
    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}"
    if count > 1 and not allow_multi_edit:
        return (
            f"Error: old_str matches {count} times in {path}. "
            "Include surrounding text to make the match unique, "
            "or set allow_multi_edit to replace all matches."
        )
    write_file(path, content.replace(old_str, new_str))
    return f"Replaced {count} match(es) in {path}"


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return its combined stdout and stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_skill",
            "description": "Load a skill by name and return its full instructions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the skill to read",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a text file or overwrite its existing contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to write"},
                    "content": {"type": "string", "description": "Full file contents"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": (
                "Replace exact text in a file. Include surrounding text to make "
                "old_str match exactly once, or set allow_multi_edit to replace all matches."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to edit"},
                    "old_str": {"type": "string", "description": "Nonempty exact text to find"},
                    "new_str": {"type": "string", "description": "Replacement text"},
                    "allow_multi_edit": {
                        "type": "boolean",
                        "description": "Replace every match instead of rejecting multiple matches",
                    },
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "read_skill": read_skill,
    "write_file": write_file,
    "str_replace": str_replace,
}
