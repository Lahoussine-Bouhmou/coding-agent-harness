import json

from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS
from ui import UI


def main():
    ui = UI()
    ui.banner()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        prompt = ui.ask()
        if not prompt:
            break
        messages.append({"role": "user", "content": prompt})

        while True:
            with ui.working():
                message, usage = call_llm(messages)
            messages.append(message.model_dump(exclude_none=True))
            ui.usage(usage)

            if message.content:
                ui.agent(message.content)
            if not message.tool_calls:
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

    ui.summary()


if __name__ == "__main__":
    main()
