import json
import os

from openai import OpenAI

from tools import TOOLS, TOOL_SCHEMAS


SYSTEM_PROMPT = (
    "You are a coding agent. Write code to solve the user's request. "
    "Use bash to inspect the workspace and read_file to read files. "
    "Respond to the user when the task is complete. "
    f"Your current working directory is: {os.getcwd()}"
)


def call_llm(messages):
    client = OpenAI(
        api_key=os.environ["API_KEY"],
        base_url=os.environ["BASE_URL"],
    )
    response = client.chat.completions.create(
        model=os.environ.get("MODEL", "deepseek/deepseek-v4-flash"),
        messages=messages,
        tools=TOOL_SCHEMAS,
    )
    usage = None
    if response.usage is not None:
        details = response.usage
        usage = {
            "prompt_tokens": details.prompt_tokens,
            "completion_tokens": details.completion_tokens,
            "reasoning_tokens": getattr(details.completion_tokens_details, "reasoning_tokens", None),
            "cached_tokens": getattr(details.prompt_tokens_details, "cached_tokens", None),
        }
    return response.choices[0].message, usage


def main():
    prompt = input("Enter your prompt> ")
    message, usage = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    if message.content:
        print(f"\nAgent: {message.content}\n")
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        print(f"\nTool: {name} {args}")
        print(TOOLS[name](**args))
    if usage is not None:
        print(usage)


if __name__ == "__main__":
    main()
