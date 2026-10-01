"""User configuration persistence.

Reads and writes recursivist's JSON settings file, resolving its location with Typer's
platform-aware application directory. The only stored preference is currently the icon
style.
"""

import json
from pathlib import Path
from typing import Any, Literal, get_args

import typer

APP_NAME = "recursivist"

IconStyle = Literal["emoji", "nerd"]
"""Icon styles accepted by ``--icon-style`` and the ``icon-style`` config key."""

ICON_STYLES: tuple[str, ...] = get_args(IconStyle)

CONFIG_KEYS: dict[str, tuple[str, ...]] = {"icon_style": ICON_STYLES}
"""Recognized configuration keys (in their stored, underscored form) mapped to the
values each one accepts."""


def get_config_path() -> Path:
    """Return the path to the configuration file.

    The location is resolved with `typer.get_app_dir`, so it follows each platform's
    convention for application data. Nothing is created on disk: the file and its
    directory may not exist until `save_config` writes them.

    Returns:
        Path to ``config.json`` inside the application directory.
    """
    return Path(typer.get_app_dir(APP_NAME)) / "config.json"


def load_config() -> dict[str, Any]:
    """Load the user configuration from disk.

    Reading never writes: a missing configuration directory is left missing.

    Returns:
        The parsed configuration mapping, or the default ``{"icon_style": "emoji"}``
        when the file is missing, unreadable, or does not contain a JSON object.
    """
    try:
        config_path = get_config_path()
        if config_path.is_file():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            if isinstance(config, dict):
                return config
    except (OSError, ValueError):
        pass
    return {"icon_style": "emoji"}


def save_config(config: dict[str, Any]) -> None:
    """Write the user configuration to disk as indented JSON.

    Creates the configuration directory if it does not already exist.

    Args:
        config: Configuration mapping to persist. Overwrites any existing file at the
            configuration path.
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
