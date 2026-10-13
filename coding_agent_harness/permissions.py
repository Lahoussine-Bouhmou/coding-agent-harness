import re
import shlex
from fnmatch import fnmatch
from pathlib import Path


PROJECT = Path.cwd().resolve()
BASH_RULES = {
    "*": "ask",
    "ls": "allow",
    "ls *": "allow",
    "pwd": "allow",
    "echo *": "allow",
    "cat *": "allow",
    "head *": "allow",
    "tail *": "allow",
    "wc *": "allow",
    "file *": "allow",
    "which *": "allow",
    "grep *": "allow",
    "rg *": "allow",
    "date": "allow",
    "git status*": "allow",
    "git diff*": "allow",
    "git log*": "allow",
    "git show*": "allow",
    "git ls-files*": "allow",
    "rm": "deny",
    "rm *": "deny",
    "sudo *": "deny",
    "chmod *": "deny",
    "chown *": "deny",
    "curl *": "deny",
    "wget *": "deny",
    "git push*": "deny",
    "git reset*": "deny",
    "git clean*": "deny",
}


def decide(command):
    """Apply the strictest rule across shell command segments."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return "ask"
    parts = [[]]
    complex_shell = bool(re.search(r"[$`\n]", command))
    for token in tokens:
        if token in ("&&", "||", ";", "|", "&"):
            parts.append([])
        elif token and all(character in "();<>|&" for character in token):
            complex_shell = True
        else:
            parts[-1].append(token)
    verdicts = []
    for part in parts:
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(" ".join(part), pattern):
                action = rule
        verdicts.append(action)
    if "deny" in verdicts:
        return "deny"
    if complex_shell or "ask" in verdicts:
        return "ask"
    return "allow"


def inside_project(path):
    return Path(path).resolve().is_relative_to(PROJECT)


def check(name, args):
    if name == "bash":
        return decide(args["command"]), f"Run: {args['command']}"
    if name in ("write_file", "str_replace") and not inside_project(args["path"]):
        return "ask", f"{name} outside {PROJECT}: {args['path']}"
    return "allow", None


def execute(name, args, ui):
    from .tools import TOOLS

    action, reason = check(name, args)
    if action == "deny":
        return f"Blocked by policy: {reason}"
    if action == "ask" and not ui.approve(reason):
        return "The user denied this tool call."
    if name == "task":
        return TOOLS[name](**args, ui=ui)
    return TOOLS[name](**args)
