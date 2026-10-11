import subprocess

from skills import read_skill


def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=60
    )
    return (result.stdout + result.stderr) or "(no output)"


def read_file(path: str) -> str:
    """Read a text file and return its contents."""
    with open(path, encoding="utf-8") as file:
        return file.read()


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
]

TOOLS = {"bash": bash, "read_file": read_file, "read_skill": read_skill}
