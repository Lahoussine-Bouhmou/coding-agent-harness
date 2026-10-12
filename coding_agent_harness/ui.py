import json

from rich.console import Console, Group
from rich.json import JSON
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


MAX_TOOL_OUTPUT_LINES = 12


class UI:
    def __init__(self):
        self.console = Console()
        self.totals = {}

    def banner(self):
        self.console.rule("Coding Agent Harness", style="blue")
        self.console.print("/sessions · /rewind · Ctrl-D or an empty prompt to exit", style="dim")

    def note(self, text):
        self.console.print(Text(text, style="dim"))

    def resumed(self, messages):
        turns = sum(message["role"] == "user" for message in messages)
        self.note(f"Resumed {len(messages)} messages · {turns} turns")

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
            answer = self.console.input("Number (empty to cancel)> ").strip()
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
            return self.console.input("\n[bold green]>[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return ""

    def working(self):
        return self.console.status("Thinking…", spinner="dots")

    def agent(self, text):
        self.console.print()
        self.console.print("Agent", style="bold blue")
        self.console.print(Markdown(text))

    def tool(self, name, args, result):
        arguments = (
            str(next(iter(args.values()))) if len(args) == 1 else json.dumps(args)
        )
        lines = result.splitlines() or ["(no output)"]
        body = Text("\n".join(lines[:MAX_TOOL_OUTPUT_LINES]))
        hidden = len(lines) - MAX_TOOL_OUTPUT_LINES
        if hidden > 0:
            body.append(f"\n… {hidden} more lines", style="dim italic")
        self.console.print(Panel(
            Group(Text(arguments, style="dim"), body),
            title=Text(name, style="bold yellow"),
            border_style="dim",
        ))

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
