MARKS = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}
PLAN = []


def write_plan(steps):
    """Replace the plan, allowing at most one task in progress."""
    if not isinstance(steps, list):
        return "Error: steps must be a list."
    for step in steps:
        if not isinstance(step, dict):
            return "Error: each step must be an object."
        for key in ("content", "activeForm", "status"):
            if not isinstance(step.get(key), str) or not step[key].strip():
                return f"Error: each step needs a nonempty {key} string."
        if step["status"] not in MARKS:
            return "Error: status must be pending, in_progress, or done."
    if sum(step["status"] == "in_progress" for step in steps) > 1:
        return "Error: only one task may be in_progress."
    PLAN[:] = [dict(step) for step in steps]
    return plan_prompt() or "Plan cleared."


def plan_prompt():
    return "\n".join(f"{MARKS[step['status']]} {step['content']}" for step in PLAN)


def active_form():
    for step in PLAN:
        if step["status"] == "in_progress":
            return step["activeForm"]
    return "Thinking…"


PLAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_plan",
        "description": (
            "Replace the complete plan for a multi-step task. Keep one task "
            "in_progress while working and mark all tasks done when finished."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Task description, e.g. Create the script",
                            },
                            "activeForm": {
                                "type": "string",
                                "description": "Activity label, e.g. Creating the script",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "done"],
                            },
                        },
                        "required": ["content", "activeForm", "status"],
                    },
                },
            },
            "required": ["steps"],
        },
    },
}
