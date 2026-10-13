import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment():
    load_dotenv(Path.cwd() / ".env", override=False)
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
    load_dotenv(Path.home() / ".agents" / "env", override=False)


load_environment()
CONTEXT_WINDOW = int(os.environ.get("CONTEXT_WINDOW", "128000"))
if CONTEXT_WINDOW <= 0:
    raise ValueError("CONTEXT_WINDOW must be a positive token count.")
COMPACT_AT = 0.85
COMPACT_TO = 0.35


def load_settings():
    """Load configuration while giving exported variables precedence."""
    load_environment()
    missing = [name for name in ("API_KEY", "BASE_URL") if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            f"Missing configuration: {', '.join(missing)}. "
            "Set these values in .env or ~/.agents/env."
        )
    return {
        "api_key": os.environ["API_KEY"],
        "base_url": os.environ["BASE_URL"],
        "model": os.environ.get("MODEL", "deepseek/deepseek-v4-flash"),
    }
