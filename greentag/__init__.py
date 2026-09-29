"""AI-assisted green tagging of public investment project proposals (demo)."""
__version__ = "0.1.0"

import os as _os
from pathlib import Path as _Path


def _load_dotenv() -> None:
    """Read KEY=VALUE lines from a .env file in the project root (no extra dependency)."""
    env = _Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if v.strip():
                _os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()
