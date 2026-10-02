"""User and project configuration.

Preferences come from two layers. The *user* layer is recursivist's JSON settings file,
whose location is resolved with Typer's platform-aware application directory and which
``recursivist config set`` writes. The *project* layer is a TOML file that lives with
the directory being scanned: either a dedicated ``.recursivist.toml`` or a
``[tool.recursivist]`` table in ``pyproject.toml``.

[`resolve_config`][recursivist.config.resolve_config] merges them, each layer overriding
the ones before it: built-in defaults, then the user file, then the project file. A
command-line flag overrides all three. The only preference is currently the icon style.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Literal, get_args

import typer

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

logger = logging.getLogger(__name__)

APP_NAME = "recursivist"

PROJECT_CONFIG_FILE = ".recursivist.toml"
"""Dedicated project configuration file, holding the settings at its top level."""

PYPROJECT_FILE = "pyproject.toml"
"""Shared project file, holding the settings in its ``[tool.recursivist]`` table."""

PYPROJECT_TABLE = "recursivist"

IconStyle = Literal["emoji", "nerd"]
"""Icon styles accepted by ``--icon-style`` and the ``icon-style`` config key."""

ICON_STYLES: tuple[str, ...] = get_args(IconStyle)

CONFIG_KEYS: dict[str, tuple[str, ...]] = {"icon_style": ICON_STYLES}
"""Recognized configuration keys (in their stored, underscored form) mapped to the
values each one accepts."""

DEFAULT_CONFIG: dict[str, Any] = {"icon_style": "emoji"}
"""Built-in value of every configuration key, used when no layer sets it."""


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


def _read_toml(path: Path) -> dict[str, Any]:
    """Parse the TOML file at *path*.

    Raises:
        OSError: If the file cannot be read.
        tomllib.TOMLDecodeError: If the file is not valid TOML.
    """
    with open(path, "rb") as f:
        return tomllib.load(f)


def _project_table_in(directory: Path) -> tuple[Path, Any] | None:
    """Return the project configuration stored directly in *directory*, if any.

    A ``.recursivist.toml`` is always the project's configuration, so when it cannot be
    parsed a warning is logged and it counts as an empty one. A ``pyproject.toml``
    belongs to other tools as well: it only counts when it has a ``[tool.recursivist]``
    table, and one that cannot be parsed is skipped quietly. When both files are present
    the dedicated one wins and ``pyproject.toml`` is not consulted.

    Args:
        directory: Directory to look in. Its parents are not searched.

    Returns:
        A ``(path, table)`` pair naming the file and its unvalidated settings, or
        ``None`` when *directory* holds no project configuration.
    """
    dedicated = directory / PROJECT_CONFIG_FILE
    if os.path.isfile(dedicated):
        try:
            return dedicated, _read_toml(dedicated)
        except (OSError, tomllib.TOMLDecodeError) as e:
            logger.warning("Ignoring project configuration %s: %s", dedicated, e)
            return dedicated, {}

    pyproject = directory / PYPROJECT_FILE
    if os.path.isfile(pyproject):
        try:
            tool = _read_toml(pyproject).get("tool")
        except (OSError, tomllib.TOMLDecodeError) as e:
            logger.debug("Could not read %s: %s", pyproject, e)
            return None
        if isinstance(tool, dict) and PYPROJECT_TABLE in tool:
            return pyproject, tool[PYPROJECT_TABLE]
    return None


def _validate_project_table(table: Any, source: Path) -> dict[str, Any]:
    """Keep the recognized, valid settings of a project configuration table.

    Keys may be written with dashes or underscores (``icon-style`` or ``icon_style``).
    An unknown key or an unacceptable value is reported with a warning and dropped, so a
    typo in one setting leaves that setting to the lower layers without discarding the
    rest of the file.

    Args:
        table: The parsed settings, as found in the file.
        source: The file they came from, used in warnings.

    Returns:
        The valid settings, keyed in their underscored form.
    """
    if not isinstance(table, dict):
        logger.warning(
            "Ignoring project configuration in %s: expected a table of settings",
            source,
        )
        return {}

    settings: dict[str, Any] = {}
    for raw_key, value in table.items():
        key = raw_key.replace("-", "_")
        allowed_values = CONFIG_KEYS.get(key)
        if allowed_values is None:
            valid_keys = ", ".join(k.replace("_", "-") for k in CONFIG_KEYS)
            logger.warning(
                "Ignoring unknown configuration key '%s' in %s. Valid keys: %s.",
                raw_key,
                source,
                valid_keys,
            )
        elif not isinstance(value, str) or value not in allowed_values:
            choices = " or ".join(f"'{v}'" for v in allowed_values)
            logger.warning(
                "Ignoring invalid value for '%s' in %s: %r. Use %s.",
                raw_key,
                source,
                value,
                choices,
            )
        else:
            settings[key] = value
    return settings


def load_project_config(start_dir: Path) -> dict[str, Any]:
    """Load the project configuration that applies to *start_dir*.

    Looks in *start_dir* and then in each of its parents, and uses the first directory
    that holds a project configuration: a ``.recursivist.toml``, or a ``pyproject.toml``
    with a ``[tool.recursivist]`` table. The nearest file wins outright; files further
    up are not merged in. Reading never writes.

    Args:
        start_dir: Directory the search starts from, normally the one being scanned.

    Returns:
        The valid settings of the nearest project configuration, keyed in their
        underscored form, or an empty mapping when there is none.
    """
    try:
        start = start_dir.resolve()
    except (OSError, RuntimeError):
        start = start_dir.absolute()

    for directory in (start, *start.parents):
        found = _project_table_in(directory)
        if found is not None:
            source, table = found
            logger.debug("Using project configuration from %s", source)
            return _validate_project_table(table, source)
    return {}


def resolve_config(project_dir: Path | None = None) -> dict[str, Any]:
    """Return the effective configuration for a run.

    Layers are applied in order, each overriding the previous one: the built-in
    defaults, the user configuration file, then the project configuration that applies
    to *project_dir*.

    Args:
        project_dir: Directory whose project configuration should apply, normally the
            one being scanned. ``None`` skips the project layer, leaving the user
            configuration over the defaults.

    Returns:
        The merged configuration mapping, with every key in `CONFIG_KEYS` present.
    """
    config = {**DEFAULT_CONFIG, **load_config()}
    if project_dir is not None:
        config.update(load_project_config(project_dir))
    return config
