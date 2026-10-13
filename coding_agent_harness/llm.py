import json
import os
from openai import OpenAI

from .config import load_settings
from .skills import skills_prompt
from .permissions import execute
from .tools import TOOL_SCHEMAS
from .ui import UI


SYSTEM_PROMPT = (
    "You are a coding agent. Write code to solve the user's request. "
    "Use bash to inspect the workspace and read_file to read files. "
    "Use write_file to create files and str_replace for targeted edits. "
    "Large tool outputs are capped and include a temporary file path to the full "
    "output. Read sections with head, tail, sed, or grep during the current turn. "
    "The temporary file is removed when the turn ends; rerun the command later if needed. "
    "Respond to the user when the task is complete. "
    "For multi-step tasks, call write_plan first with a plan. Send the whole "
    "list each time because it replaces the previous list. Keep one task "
    "in_progress while working. As soon as it is finished, mark it done and "
    "start the next task in the same update. Mark all tasks done when finished. "
    "Skip plan tracking for single-step tasks. The current plan appears in "
    "<plan> in the request context; use it as the current task state. "
    f"Your current working directory is: {os.getcwd()}\n\n"
    "Skills provide instructions for specific tasks. When a skill matches the "
    "user's request, call read_skill first and follow its instructions.\n\n"
    f"Available skills:\n{skills_prompt()}"
)


def call_llm(messages):
    settings = load_settings()
    client = OpenAI(
        api_key=settings["api_key"],
        base_url=settings["base_url"],
    )
    response = client.chat.completions.create(
        model=settings["model"],
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
        print(execute(name, args, UI()))
    if usage is not None:
        print(usage)


if __name__ == "__main__":
    main()
