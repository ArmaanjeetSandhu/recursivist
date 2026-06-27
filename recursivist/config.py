"""User configuration persistence.

Reads and writes recursivist's JSON settings file, resolving its location
with Typer's platform-aware application directory. The only stored preference
is currently the icon style.
"""

import json
from pathlib import Path
from typing import Any

import typer

APP_NAME = "recursivist"


def get_config_path() -> Path:
    """Return the path to the configuration file, creating its directory.

    The location is resolved with :func:`typer.get_app_dir`, so it follows
    each platform's convention for application data. The parent directory is
    created if it does not already exist.

    Returns:
        Path to ``config.json`` inside the application directory.
    """
    app_dir = typer.get_app_dir(APP_NAME)
    config_dir = Path(app_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict[str, Any]:
    """Load the user configuration from disk.

    Returns:
        The parsed configuration mapping, or the default
        ``{"icon_style": "emoji"}`` when the file is missing, unreadable, or
        does not contain a JSON object.
    """
    config_path = get_config_path()
    if config_path.is_file():
        try:
            with open(config_path) as f:
                config = json.load(f)
                if isinstance(config, dict):
                    return config
        except json.JSONDecodeError:
            pass
    return {"icon_style": "emoji"}


def save_config(config: dict[str, Any]) -> None:
    """Write the user configuration to disk as indented JSON.

    Args:
        config: Configuration mapping to persist. Overwrites any existing
            file at the configuration path.
    """
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
