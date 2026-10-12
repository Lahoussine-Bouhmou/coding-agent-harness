import os
from pathlib import Path

from dotenv import load_dotenv


def load_settings():
    """Load configuration while giving exported variables precedence."""
    load_dotenv(Path.cwd() / ".env", override=False)
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
    load_dotenv(Path.home() / ".agents" / "env", override=False)
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
