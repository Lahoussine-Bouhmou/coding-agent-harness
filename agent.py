import json

from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS


def main():
    prompt = input("Enter your prompt> ")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    while True:
        message, usage = call_llm(messages)
        messages.append(message.model_dump(exclude_none=True))

        if message.content:
            print(f"\nAgent: {message.content}\n")
        if usage is not None:
            print(usage)
        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"\nTool: {name} {args}")
            result = TOOLS[name](**args)
            print(result)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


if __name__ == "__main__":
    main()
