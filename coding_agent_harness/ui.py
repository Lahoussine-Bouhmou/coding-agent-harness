import json

from rich.console import Console, Group
from rich.json import JSON
from rich.markdown import Markdown
from rich.panel import Panel
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from . import prompt
from .plan import MARKS


MAX_TOOL_OUTPUT_LINES = 12


class UI:
    def __init__(self):
        self.console = Console()
        self.totals = {}

    def banner(self, sandbox_name="none"):
        self.console.rule("Coding Agent Harness", style="blue")
        self.console.print("/sessions · /rewind · /compact · Alt-Enter for a newline · Ctrl-D to exit", style="dim")
        self.note(f"Sandbox: {sandbox_name}")
        if sandbox_name == "none":
            self.note("Shell commands are unsandboxed; permission checks still apply.")

    def note(self, text):
        self.console.print(Text(text, style="dim"))

    def approve(self, reason):
        self.console.print(Text(reason, style="bold yellow"))
        try:
            answer = prompt.read("Allow? (y/n)> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return False
        return answer in ("y", "yes")

    def clear(self):
        self.console.clear()

    def resumed(self, messages, label="Resumed"):
        turns = sum(message["role"] == "user" for message in messages)
        self.note(f"{label} {len(messages)} messages · {turns} turns")

    def replay(self, messages):
        results = {
            message["tool_call_id"]: message["content"]
            for message in messages if message["role"] == "tool"
        }
        for message in messages:
            if message["role"] == "user":
                self.console.print(Text(f"\n> {message['content']}", style="bold green"))
            elif message["role"] == "assistant":
                if message.get("content"):
                    self.agent(message["content"])
                for call in message.get("tool_calls") or []:
                    self.tool(
                        call["function"]["name"],
                        json.loads(call["function"]["arguments"]),
                        results.get(call["id"], ""),
                    )

    def pick(self, title, rows):
        self.console.print(Text(title, style="bold blue"))
        for index, row in enumerate(rows):
            self.console.print(Text(f"{index:>3}  {row}"))
        try:
            answer = prompt.read("Number (empty to cancel)> ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return None
        if answer.isdigit() and int(answer) < len(rows):
            return int(answer)
        return None

    def injection(self, text):
        self.console.print(Panel(Text(text, style="dim"), title="Environment context", border_style="dim"))

    def debug(self, data):
        self.console.print(Panel(JSON.from_data(data), title="Raw response", border_style="yellow"))

    def ask(self):
        try:
            self.console.print()
            return prompt.read("> ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return ""

    def working(self, label="Thinking…"):
        return self.console.status(Text(label), spinner="dots")

    def agent(self, text):
        self.console.print()
        self.console.print("Agent", style="bold blue")
        self.console.print(Markdown(text))

    def tool(self, name, args, result, nested=False):
        if name == "write_plan" and args.get("steps") and result.startswith(("[ ]", "[~]", "[x]")):
            self.plan(args["steps"])
            return
        arguments = (
            str(next(iter(args.values()))) if len(args) == 1 else json.dumps(args)
        )
        lines = result.splitlines() or ["(no output)"]
        body = Text("\n".join(lines[:MAX_TOOL_OUTPUT_LINES]))
        hidden = len(lines) - MAX_TOOL_OUTPUT_LINES
        if hidden > 0:
            body.append(f"\n… {hidden} more lines", style="dim italic")
        panel = Panel(
            Group(Text(arguments, style="dim"), body),
            title=Text(name, style="bold yellow"),
            border_style="dim",
        )
        self.console.print(Padding(panel, (0, 0, 0, 4)) if nested else panel)

    def subagent(self, description):
        self.console.print(Panel(Text(description), title="Subagent · separate conversation", border_style="blue"))

    def plan(self, steps):
        styles = {"pending": "dim", "in_progress": "bold blue", "done": "dim strike"}
        rows = Table.grid(padding=(0, 1))
        rows.add_column(no_wrap=True)
        rows.add_column(overflow="fold")
        for step in steps:
            status = step["status"]
            rows.add_row(
                Text(MARKS[status], style=styles[status]),
                Text(step["content"], style=styles[status]),
            )
        done = sum(step["status"] == "done" for step in steps)
        self.console.print(Panel(rows, title=f"Plan {done}/{len(steps)}", border_style="blue"))

    def usage(self, stats):
        if stats is None:
            return
        for key, value in stats.items():
            self.totals[key] = self.totals.get(key, 0) + (value or 0)
        details = " · ".join(
            f"{value:,} {key.replace('_tokens', '')}"
            for key, value in stats.items() if value
        )
        self.console.print(Text(details, style="dim"))

    def summary(self):
        if not self.totals:
            return
        self.console.rule("Session token usage", style="blue")
        table = Table.grid(padding=(0, 2))
        table.add_column(style="dim")
        table.add_column(justify="right")
        for key, value in self.totals.items():
            table.add_row(key.replace("_", " "), f"{value:,}")
        self.console.print(table)

    def compacted(self, before, messages):
        summary = next(
            message["content"] for message in reversed(messages)
            if (message.get("content") or "").startswith("<summary>")
        )
        self.console.print(Panel(
            Markdown(summary.removeprefix("<summary>").removesuffix("</summary>")),
            title=f"Compacted · {before} → {len(messages)} messages",
            border_style="blue",
        ))
