import json
import os
import subprocess

from openai import OpenAI


BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command and return its output.",
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
}


def bash(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def main():
    client = OpenAI(
        api_key=os.environ["API_KEY"],
        base_url=os.environ["BASE_URL"],
    )
    prompt = input("Enter your prompt> ")
    response = client.chat.completions.create(
        model=os.environ.get("MODEL", "deepseek/deepseek-v4-flash"),
        messages=[
            {
                "role": "system",
                "content": "You are a coding agent. Write code to solve the user's request. Use the bash tool to inspect files.",
            },
            {"role": "user", "content": prompt},
        ],
        tools=[BASH_TOOL],
    )
    message = response.choices[0].message
    if message.content:
        print(f"\nAgent: {message.content}\n")
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        command = json.loads(tool_call.function.arguments)["command"]
        print(f"\nTool: bash {command}")
        print(bash(command))
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
