import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT = Path.cwd().resolve()


def name():
    if sys.platform == "darwin" and shutil.which("sandbox-exec"):
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bubblewrap"
    return "none"


def wrap(command):
    backend = name()
    if backend == "seatbelt":
        project = json.dumps(str(PROJECT))
        git_dir = json.dumps(str(PROJECT / ".git"))
        profile = (
            "(version 1)\n"
            "(deny default)\n"
            "(allow process-exec process-fork signal)\n"
            "(allow file-read*)\n"
            "(allow sysctl-read)\n"
            "(deny network*)\n"
            f'(allow file-write* (subpath {project}) (literal "/dev/null"))\n'
            f"(deny file-write* (subpath {git_dir}))\n"
        )
        return ["sandbox-exec", "-p", profile, "/bin/sh", "-c", command]
    if backend == "bubblewrap":
        args = [
            "bwrap",
            "--ro-bind", "/", "/",
            "--bind", str(PROJECT), str(PROJECT),
        ]
        if (PROJECT / ".git").exists():
            args.extend(["--ro-bind", str(PROJECT / ".git"), str(PROJECT / ".git")])
        args.extend([
            "--dev", "/dev", "--proc", "/proc",
            "--unshare-net", "--unshare-pid", "--new-session", "--die-with-parent",
            "--chdir", str(PROJECT),
            "/bin/sh", "-c", command,
        ])
        return args
    return None


def run(command, timeout=60):
    """Use the available OS sandbox; never retry a failed sandbox unsandboxed."""
    wrapped = wrap(command)
    return subprocess.run(
        wrapped if wrapped is not None else command,
        shell=wrapped is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
