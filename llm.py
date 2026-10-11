import json
import os

from openai import OpenAI

from tools import TOOLS, TOOL_SCHEMAS


def main():
    client = OpenAI(
        api_key=os.environ["API_KEY"],
        base_url=os.environ["BASE_URL"],
    )
    prompt = input("Enter your prompt> ")
    response = client.chat.completions.create(
        model=os.environ.get("MODEL", "openrouter/free"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a coding agent. Write code to solve the user's request. "
                    "Use bash to inspect the workspace and read_file to read files. "
                    f"Your current working directory is: {os.getcwd()}"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        tools=TOOL_SCHEMAS,
    )
    message = response.choices[0].message
    if message.content:
        print(f"\nAgent: {message.content}\n")
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        print(f"\nTool: {name} {args}")
        print(TOOLS[name](**args))
    if response.usage is not None:
        usage = response.usage
        print({
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "reasoning_tokens": getattr(usage.completion_tokens_details, "reasoning_tokens", None),
            "cached_tokens": getattr(usage.prompt_tokens_details, "cached_tokens", None),
        })


if __name__ == "__main__":
    main()
