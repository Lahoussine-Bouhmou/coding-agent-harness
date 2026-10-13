import os


MAX_TURNS = 12
ALLOWED = {"bash", "read_file", "read_skill"}
SYSTEM_PROMPT = (
    "You are an exploration subagent answering one question for a lead agent. "
    "You cannot see its conversation. Only your final report returns to it. "
    f"Work inside {os.getcwd()}; do not search from / or the home directory. "
    "Use read_file, read_skill, and routine read-only bash commands to investigate. "
    "Do not modify files or run commands with side effects. Search in batches "
    "and stop when you can answer. Return concise findings, aiming for under "
    "150 words, with file paths, line numbers, and relevant function names. "
    "State what you could not verify. Large outputs include a temporary file "
    "path; read sections rather than loading the entire output again."
)


def toolset():
    from .tools import TOOL_SCHEMAS

    return [schema for schema in TOOL_SCHEMAS if schema["function"]["name"] in ALLOWED]


def task(description: str, ui=None) -> str:
    from . import history
    from .llm import call_llm
    from .tools import execute_tool
    from .ui import UI

    if ui is None:
        ui = UI()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]
    ui.subagent(description)
    report = None
    # Clean up only this explorer's output files, preserving the parent's files.
    spill_start = len(history.SPILLS)
    try:
        for _ in range(MAX_TURNS):
            history.fit(messages)
            with ui.working("Subagent exploring…"):
                message, usage = call_llm(messages, tools=toolset())
            messages.append(message.model_dump(exclude_none=True))
            ui.usage(usage)
            report = message.content or report
            if not message.tool_calls:
                return report or "The subagent returned no findings."
            for call in message.tool_calls:
                args, result = execute_tool(call, ui, allowed=ALLOWED)
                ui.tool(call.function.name, args, result, nested=True)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })
        return (
            f"Stopped after {MAX_TURNS} rounds before finishing. "
            "Narrow the question and try again.\n\n"
            + (report or "No findings were returned.")
        )
    finally:
        for path in history.SPILLS[spill_start:]:
            path.unlink(missing_ok=True)
        del history.SPILLS[spill_start:]


TASK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "task",
        "description": (
            "Send a self-contained codebase exploration question to a fresh "
            "subagent and receive its findings. It cannot see this conversation. "
            "Use it to locate implementation or trace behavior; do edits yourself."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Standalone question with scope, starting paths, and expected findings",
                },
            },
            "required": ["description"],
        },
    },
}
