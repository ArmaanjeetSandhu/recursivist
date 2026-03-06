import json
from pathlib import Path
from typing import Any

import typer

APP_NAME = "recursivist"


def get_config_path() -> Path:
    """Return the cross-platform path to the config file."""
    app_dir = typer.get_app_dir(APP_NAME)
    config_dir = Path(app_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict[str, Any]:
    """Load configuration from the JSON file."""
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
    """Save configuration to the JSON file."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
