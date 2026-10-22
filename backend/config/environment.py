"""Project environment loading.

The process environment always wins.  ``backend/.env`` is an optional local
convenience file and is never required in production.
"""
from pathlib import Path

from dotenv import load_dotenv


def load_project_environment(path: Path) -> bool:
    """Load an optional dotenv file without overriding host-supplied values."""
    return load_dotenv(dotenv_path=path, override=False)