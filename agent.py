import argparse
import json

import commands
import session

from context import reminder
from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS
from ui import UI


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the latest saved session")
    parser.add_argument("--debug", action="store_true", help="show raw model responses")
    cli = parser.parse_args(argv)
    ui = UI()
    ui.banner()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if cli.resume:
        saved = session.all_sessions()
        if saved:
            messages = session.open_session(saved[0]["id"])
            ui.resumed(messages)
        else:
            ui.note("No saved conversations yet. Starting a new session.")

    while True:
        prompt = ui.ask()
        if not prompt:
            break
        if prompt.startswith("/"):
            messages = commands.handle(prompt, messages, ui)
            continue
        messages.append({"role": "user", "content": prompt})

        while True:
            injection = reminder()
            ui.injection(injection["content"])
            with ui.working():
                message, usage = call_llm(messages + [injection])
            messages.append(message.model_dump(exclude_none=True))
            ui.usage(usage)
            if cli.debug:
                ui.debug(message.model_dump(exclude_none=True))

            if message.content:
                ui.agent(message.content)
            if not message.tool_calls:
                session.save(messages)
                break

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                result = TOOLS[name](**args)
                ui.tool(name, args, result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
            session.save(messages)

    ui.summary()


if __name__ == "__main__":
    main()
