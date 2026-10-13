import json
import subprocess

from . import sandbox
from . import history

from .context import note_read
from .skills import read_skill
from .plan import PLAN_SCHEMA, write_plan
from .subagent import TASK_SCHEMA, task


def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    try:
        result = sandbox.run(command)
    except subprocess.TimeoutExpired as error:
        return f"Timed out after {error.timeout}s. Narrow the command or search scope and try again."
    return history.cap((result.stdout + result.stderr) or "(no output)")


def read_file(path: str) -> str:
    """Read a text file and return its contents."""
    with open(path, encoding="utf-8") as file:
        content = file.read()
    note_read(path)
    return history.cap(content)


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
    with open(path, encoding="utf-8") as file:
        content = file.read()
    note_read(path)
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


def execute_tool(tool_call, ui, allowed=None):
    """Validate a model tool call and return errors through the tool protocol."""
    from .permissions import check, execute

    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments)
    except (json.JSONDecodeError, TypeError):
        return {}, "Error: tool arguments must be valid JSON."
    if not isinstance(args, dict):
        return {}, "Error: tool arguments must be a JSON object."
    if name not in TOOLS:
        return args, f"Error: unknown tool '{name}'. Available: {', '.join(TOOLS)}."
    if allowed is not None and name not in allowed:
        return args, f"Error: tool '{name}' is unavailable to this exploration subagent."
    try:
        if allowed is not None and name == "bash" and check(name, args)[0] != "allow":
            return args, "Blocked: exploration subagents may only run commands allowed automatically by policy."
        return args, execute(name, args, ui)
    except (TypeError, KeyError) as error:
        return args, f"Error: invalid arguments for {name}: {error}"
    except Exception as error:
        return args, f"Error: {name} failed ({type(error).__name__}): {error}"


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
    PLAN_SCHEMA,
    TASK_SCHEMA,
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "read_skill": read_skill,
    "write_file": write_file,
    "str_replace": str_replace,
    "write_plan": write_plan,
    "task": task,
}
