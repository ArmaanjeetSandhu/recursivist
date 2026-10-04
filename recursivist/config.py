"""User and project configuration.

Preferences come from two layers. The *user* layer is recursivist's JSON settings file,
whose location is resolved with Typer's platform-aware application directory and which
``recursivist config set`` writes. The *project* layer is a TOML file that lives with
the directory being scanned: either a dedicated ``.recursivist.toml`` or a
``[tool.recursivist]`` table in ``pyproject.toml``.

[`resolve_config`][recursivist.config.resolve_config] merges them, each layer overriding
the ones before it: built-in defaults, then the user file, then the project file. A
command-line flag overrides all three. The only preference is currently the icon style.

[`resolve_config_layers`][recursivist.config.resolve_config_layers] gives the same
resolution layer by layer, naming the file each value comes from. It is what
``recursivist config list`` prints.

Both files can be edited by hand, so both are validated as they are loaded: an unknown
key or an unacceptable value is reported with a warning and left out, and the setting
falls through to the layer below.
"""

import json
import logging
import os
import shlex
import sys
from dataclasses import dataclass
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

LAYER_PROJECT = "project"
"""Name of the layer read from the project configuration file."""

LAYER_USER = "user"
"""Name of the layer read from the user configuration file."""

LAYER_DEFAULT = "default"
"""Name of the layer holding the built-in defaults."""


@dataclass(frozen=True)
class ConfigLayer:
    """What one configuration layer holds for a single setting.

    Attributes:
        name: The layer: `LAYER_PROJECT`, `LAYER_USER`, or `LAYER_DEFAULT`.
        value: The layer's value for the setting, or ``None`` when the layer does not
            set it. A value the setting does not accept counts as not set. The default
            layer always has a value.
        source: The file the layer is read from, or ``None`` when there is none: no
            project configuration applies, the user configuration file does not exist,
            or the layer is the built-in defaults.
    """

    name: str
    value: str | None
    source: Path | None


def get_config_path() -> Path:
    """Return the path to the configuration file.

    The location is resolved with `typer.get_app_dir`, so it follows each platform's
    convention for application data. Nothing is created on disk: the file and its
    directory may not exist until `save_config` writes them.

    Returns:
        Path to ``config.json`` inside the application directory.
    """
    return Path(typer.get_app_dir(APP_NAME)) / "config.json"


def read_config_file() -> dict[str, Any]:
    """Read the user configuration file exactly as it is stored.

    Nothing is validated, so the mapping may hold keys and values that recursivist does
    not recognize. It is what ``recursivist config set`` and ``config unset`` edit, so
    that changing one setting leaves the rest of the file untouched. Use `load_config`
    for settings that are safe to act on.

    A file that cannot be read, is not valid JSON, or does not hold a JSON object is
    reported with a warning and treated as empty. Reading never writes: a missing
    configuration directory is left missing.

    Returns:
        The stored mapping, or an empty one when the file is missing or unusable.
    """
    config_path = get_config_path()
    if not os.path.isfile(config_path):
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, ValueError) as e:
        logger.warning("Ignoring user configuration %s: %s", config_path, e)
        return {}
    if not isinstance(config, dict):
        logger.warning(
            "Ignoring user configuration %s: expected a JSON object", config_path
        )
        return {}
    return config


def load_config() -> dict[str, Any]:
    """Load the valid settings of the user configuration file.

    The file is validated as it is loaded, so a hand-edited mistake never reaches the
    rest of the program: an unknown key or an unacceptable value is reported with a
    warning and left out. The warning for an unknown key gives the ``recursivist config
    unset`` command that removes it. Keys may be written with dashes or underscores.
    Reading never writes, so the file itself is left as it is.

    Returns:
        The valid settings, keyed in their underscored form. Settings the file does not
        set, or sets wrongly, are absent; the mapping is empty when the file is missing
        or unusable. Use `resolve_config` for a mapping with every key present.
    """
    return _validate_settings(read_config_file(), get_config_path(), unset_hint=True)


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


def _unset_command(key: str) -> str:
    """Return the shell command that removes *key* from the user configuration.

    The key comes from a hand-edited file, so it is quoted for the shell, and one that
    starts with a dash is placed after ``--`` so it is not read as an option.
    """
    separator = "-- " if key.startswith("-") else ""
    return f"{APP_NAME} config unset {separator}{shlex.quote(key)}"


def _validate_settings(
    table: dict[str, Any], source: Path, *, unset_hint: bool = False
) -> dict[str, Any]:
    """Keep the recognized, valid settings of a configuration file.

    Keys may be written with dashes or underscores (``icon-style`` or ``icon_style``).
    An unknown key or an unacceptable value is reported with a warning and dropped, so a
    typo in one setting leaves that setting to the lower layers without discarding the
    rest of the file.

    Args:
        table: The parsed settings, as found in the file.
        source: The file they came from, used in warnings.
        unset_hint: Whether the warning for an unknown key should end with the
            ``recursivist config unset`` command that removes it. Only meaningful for
            the user configuration file, which is the one that command edits.

    Returns:
        The valid settings, keyed in their underscored form.
    """
    settings: dict[str, Any] = {}
    for raw_key, value in table.items():
        key = raw_key.replace("-", "_")
        allowed_values = CONFIG_KEYS.get(key)
        if allowed_values is None:
            valid_keys = ", ".join(k.replace("_", "-") for k in CONFIG_KEYS)
            hint = (
                f" To remove it, run: {_unset_command(raw_key)}" if unset_hint else ""
            )
            logger.warning(
                "Ignoring unknown configuration key '%s' in %s. Valid keys: %s.%s",
                raw_key,
                source,
                valid_keys,
                hint,
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


def _validate_project_table(table: Any, source: Path) -> dict[str, Any]:
    """Keep the recognized, valid settings of a project configuration table.

    A ``[tool.recursivist]`` entry that is not a table is reported with a warning and
    counts as empty; otherwise the settings are checked by `_validate_settings`.

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
    return _validate_settings(table, source)


def _find_project_config(start_dir: Path) -> tuple[Path, dict[str, Any]] | None:
    """Find the project configuration that applies to *start_dir*.

    Looks in *start_dir* and then in each of its parents, and uses the first directory
    that holds a project configuration: a ``.recursivist.toml``, or a ``pyproject.toml``
    with a ``[tool.recursivist]`` table. The nearest file wins outright; files further
    up are not merged in. Reading never writes.

    Args:
        start_dir: Directory the search starts from, normally the one being scanned.

    Returns:
        A ``(path, settings)`` pair naming the nearest project configuration file and
        holding its valid settings, keyed in their underscored form, or ``None`` when
        there is no such file.
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
            return source, _validate_project_table(table, source)
    return None


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
    found = _find_project_config(start_dir)
    return found[1] if found is not None else {}


def resolve_config_layers(
    project_dir: Path | None = None,
) -> dict[str, list[ConfigLayer]]:
    """Return what every configuration layer holds for each setting.

    The layers of a setting are listed from the highest precedence to the lowest: the
    project configuration that applies to *project_dir*, the user configuration file,
    then the built-in default. The first layer that has a value is the one in effect,
    and the default layer always has one. Both files are validated as they are loaded,
    so every value is one its key accepts, and a layer whose file sets a key wrongly
    counts as not setting it. Reading never writes.

    Args:
        project_dir: Directory whose project configuration should apply, normally the
            one being scanned. ``None`` leaves the project layer out altogether.

    Returns:
        A mapping from every key in `CONFIG_KEYS` to its layers, in precedence order.
    """
    user_path = get_config_path()
    user_settings = load_config()
    layers: list[tuple[str, dict[str, Any], Path | None]] = [
        (LAYER_USER, user_settings, user_path if os.path.isfile(user_path) else None),
        (LAYER_DEFAULT, DEFAULT_CONFIG, None),
    ]
    if project_dir is not None:
        source, settings = _find_project_config(project_dir) or (None, {})
        layers.insert(0, (LAYER_PROJECT, settings, source))
    return {
        key: [
            ConfigLayer(name, settings.get(key), source)
            for name, settings, source in layers
        ]
        for key in CONFIG_KEYS
    }


def resolve_config(project_dir: Path | None = None) -> dict[str, Any]:
    """Return the effective configuration for a run.

    Layers are applied in order, each overriding the previous one: the built-in
    defaults, the user configuration file, then the project configuration that applies
    to *project_dir*. Both files are validated as they are loaded, so every value in the
    result is one its key accepts.

    Args:
        project_dir: Directory whose project configuration should apply, normally the
            one being scanned. ``None`` skips the project layer, leaving the user
            configuration over the defaults.

    Returns:
        The merged configuration mapping, with every key in `CONFIG_KEYS` present.
    """
    return {
        key: next(layer.value for layer in layers if layer.value is not None)
        for key, layers in resolve_config_layers(project_dir).items()
    }
