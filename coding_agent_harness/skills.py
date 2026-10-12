from pathlib import Path

import yaml


SKILL_DIRS = [
    Path.cwd() / ".agents" / "skills",
    Path.home() / ".agents" / "skills",
]


def find_skills():
    skills = {}
    for directory in SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            parts = text.split("---", 2)
            if len(parts) != 3 or parts[0].strip():
                continue
            try:
                metadata = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                continue
            if not isinstance(metadata, dict):
                continue
            name = metadata.get("name")
            description = metadata.get("description")
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(description, str) or not description.strip():
                continue
            skills[name] = {
                "description": " ".join(description.split()),
                "path": path,
            }
    return skills


SKILLS = find_skills()


def skills_prompt():
    return "\n".join(
        f"- {name}: {skill['description']}" for name, skill in SKILLS.items()
    )


def read_skill(name: str) -> str:
    """Read the full instructions for a discovered skill."""
    skill = SKILLS.get(name)
    if skill is None:
        return f"No skill named '{name}'."
    return skill["path"].read_text(encoding="utf-8")
