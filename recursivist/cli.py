#!/usr/bin/env python3
"""Recursivist CLI - A beautiful directory structure visualization tool.

Provides the command-line interface for the recursivist package, letting users visualize
directory structures, export them in various formats, compare two structures
side-by-side, and manage user configurations.

Main commands:
    visualize: Display a directory structure in the terminal with rich formatting and
        optional statistics.
    export: Export a directory structure to TXT, JSON, HTML, MD, SVG, or RST.
    compare: Compare two directory structures with highlighted differences.
    config: Manage persistent user preferences like the icon style, the date and size
        formats, and the ignore file.
    version: Display the current version information.

The visualize, export, and compare commands accept a GitHub repository URL anywhere they
accept a local directory; see [`recursivist.github`][recursivist.github].

All commands share a consistent set of filtering and display options:
    - Exclude directories, file extensions, glob, or regex patterns.
    - Include patterns that keep only matching files and override ignore files, but not
      the explicit exclusions above.
    - Support for .gitignore and similar ignore files.
    - Depth limitation for large directories.
    - Full-path display option.
    - File statistics with sorting by lines of code, size, or modification time.
    - Modification times in a relative or an ISO 8601 format.
    - File sizes in IEC (KiB, MiB, GiB) or SI (kB, MB, GB) units.
"""

import contextlib
import functools
import json
import logging
import os
from collections.abc import Callable, Generator
from dataclasses import dataclass, replace
from pathlib import Path
from re import Pattern
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from recursivist._models import Directory
from recursivist.compare import (
    display_comparison,
    export_comparison,
)
from recursivist.config import (
    CONFIG_KEYS,
    LIST_KEYS,
    ConfigLayer,
    DateFormat,
    IconStyle,
    SizeFormat,
    accepts_value,
    delete_config_file,
    describe_accepted_values,
    get_config_path,
    read_config_file,
    resolve_config,
    resolve_config_layers,
    save_config,
)
from recursivist.exporters import (
    canonical_extension,
    get_exporter,
    supported_formats,
)
from recursivist.filtering import (
    InvalidPatternError,
    compile_regex_patterns,
    normalize_extensions,
)
from recursivist.flags import DisplayOptions, resolve_display_options
from recursivist.git_status import GitStatusError, get_git_status
from recursivist.github import (
    GitHubTarget,
    apply_github_urls,
    checkout_repository,
    get_github_token,
    parse_github_url,
    same_github_target,
)
from recursivist.scanner import get_directory_structure
from recursivist.tree import display_tree

logger = logging.getLogger("recursivist")
app = typer.Typer(
    help="Recursivist: A beautiful directory structure visualization tool",
    add_completion=True,
)
console = Console()
err_console = Console(stderr=True)

_FLAG_ORDER_KEY = "recursivist.flag_order"


def _records_order(flag_id: str) -> Callable[[typer.Context, bool], bool]:
    """Build an option callback that notes when the parser reaches a flag.

    Flag order matters for sorting and annotation, but a command only receives *which*
    flags were given. The parser knows the order: it runs the callbacks of the options
    present on the command line in the order they appeared, ahead of those of the
    options that were left out. Each order-sensitive flag carries one of these callbacks
    and is recorded in the order the parser read it.

    Args:
        flag_id: The flag's id in the [`recursivist.flags`][recursivist.flags] registry.

    Returns:
        A callback for `typer.Option` that appends *flag_id* to the invocation's flag
        order when the flag is set, and passes the option's value through unchanged.
    """

    def record(ctx: typer.Context, value: bool) -> bool:
        if value:
            ctx.meta.setdefault(_FLAG_ORDER_KEY, []).append(flag_id)
        return value

    return record


def _flag_order(ctx: typer.Context) -> list[str]:
    """Return the ids of the order-sensitive flags, in the order they were given.

    These are the ids recorded by the `_records_order` callbacks while this command's
    arguments were parsed.
    """
    return list(ctx.meta.get(_FLAG_ORDER_KEY, []))


HELP_EXCLUDE_DIRS = (
    "Directory to exclude; repeat the flag for several (values may contain spaces). "
    "Defaults to the project config, then the user config."
)
HELP_EXCLUDE_EXTS = "File extension to exclude; repeat the flag for several"
HELP_EXCLUDE_PATTERNS = (
    "Pattern to exclude; repeat the flag for several (values may contain spaces)"
)
HELP_INCLUDE_PATTERNS = (
    "Pattern to include (overrides ignore files, but not other exclusions); "
    "repeat the flag for several"
)
HELP_USE_REGEX = "Treat patterns as regex instead of glob patterns"
HELP_IGNORE_FILE = (
    "Ignore file to use (e.g., .gitignore). Defaults to the project config, then the "
    "user config."
)
HELP_SHOW_FULL_PATH = (
    "Show full paths instead of just filenames "
    "(GitHub blob URLs for GitHub repositories)"
)
HELP_SORT_BY_LOC = "Sort files by lines of code and display LOC counts"
HELP_SORT_BY_SIZE = "Sort files by size and display file sizes"
HELP_SORT_BY_MTIME = "Sort files by modification time and display timestamps"
HELP_SORT_BY_GIT_STATUS = "Sort files by Git status and display status markers"
HELP_SORT_BY_SIMILARITY = "Group files with similar names together"
HELP_LOC = "Display lines of code without affecting sort order"
HELP_SIZE = "Display file sizes without affecting sort order"
HELP_MTIME = "Display modification times without affecting sort order"
HELP_GIT_STATUS = (
    "Display Git status markers without affecting sort order: "
    "[U] untracked, [M] modified, [A] added, [D] deleted"
)
HELP_DATE_FORMAT = (
    "Format of modification times: 'relative' (Today 14:30) or 'iso' "
    "(2026-10-07T12:30:41Z, in UTC)."
)
HELP_SIZE_FORMAT = (
    "Format of file sizes: 'iec' (powers of 1024: KiB, MiB, GiB) or 'si' "
    "(powers of 1000: kB, MB, GB)."
)
HELP_VERBOSE = "Enable verbose output"

MSG_ERROR = "Error: %s"
MSG_VERBOSE = "Verbose mode enabled"
MSG_FULL_PATH = "Showing full paths instead of just filenames"
MSG_GIT_STATUS = "Annotating files with Git status markers"
MSG_SORT_BY = {
    "loc": "Sorting files by lines of code",
    "size": "Sorting files by size",
    "mtime": "Sorting files by modification time (newest first)",
    "git_status": "Sorting files by Git status",
    "similarity": "Grouping files by name similarity",
}
MSG_DISPLAY_METRIC = {
    "loc": "Displaying lines of code",
    "size": "Displaying file sizes",
    "mtime": "Displaying modification times",
}


ExcludeDirsOption = Annotated[
    list[str] | None, typer.Option("--exclude", "-e", help=HELP_EXCLUDE_DIRS)
]
ExcludeExtensionsOption = Annotated[
    list[str] | None, typer.Option("--exclude-ext", "-x", help=HELP_EXCLUDE_EXTS)
]
ExcludePatternsOption = Annotated[
    list[str] | None,
    typer.Option("--exclude-pattern", "-p", help=HELP_EXCLUDE_PATTERNS),
]
IncludePatternsOption = Annotated[
    list[str] | None,
    typer.Option("--include-pattern", "-i", help=HELP_INCLUDE_PATTERNS),
]
UseRegexOption = Annotated[bool, typer.Option("--regex", "-r", help=HELP_USE_REGEX)]
IgnoreFileOption = Annotated[
    str | None, typer.Option("--ignore-file", "-g", help=HELP_IGNORE_FILE)
]
MaxDepthDisplayOption = Annotated[
    int,
    typer.Option("--depth", "-d", help="Maximum depth to display (0 for unlimited)"),
]
ShowFullPathOption = Annotated[
    bool, typer.Option("--full-path", "-l", help=HELP_SHOW_FULL_PATH)
]
SortByLocOption = Annotated[
    bool,
    typer.Option(
        "--sort-by-loc",
        "-s",
        help=HELP_SORT_BY_LOC,
        callback=_records_order("sort_loc"),
    ),
]
SortBySizeOption = Annotated[
    bool,
    typer.Option(
        "--sort-by-size",
        "-z",
        help=HELP_SORT_BY_SIZE,
        callback=_records_order("sort_size"),
    ),
]
SortByMtimeOption = Annotated[
    bool,
    typer.Option(
        "--sort-by-mtime",
        "-m",
        help=HELP_SORT_BY_MTIME,
        callback=_records_order("sort_mtime"),
    ),
]
SortBySimilarityOption = Annotated[
    bool,
    typer.Option(
        "--sort-by-similarity",
        "-S",
        help=HELP_SORT_BY_SIMILARITY,
        callback=_records_order("sort_similarity"),
    ),
]
SortByGitStatusOption = Annotated[
    bool,
    typer.Option(
        "--sort-by-git-status",
        help=HELP_SORT_BY_GIT_STATUS,
        callback=_records_order("sort_git"),
    ),
]
LocOption = Annotated[
    bool, typer.Option("--loc", help=HELP_LOC, callback=_records_order("disp_loc"))
]
SizeOption = Annotated[
    bool, typer.Option("--size", help=HELP_SIZE, callback=_records_order("disp_size"))
]
MtimeOption = Annotated[
    bool,
    typer.Option("--mtime", help=HELP_MTIME, callback=_records_order("disp_mtime")),
]
ShowGitStatusOption = Annotated[
    bool,
    typer.Option(
        "--git-status", "-G", help=HELP_GIT_STATUS, callback=_records_order("disp_git")
    ),
]
OutputDirOption = Annotated[
    Path | None,
    typer.Option(
        "--output-dir",
        "-o",
        help="Output directory for exports (defaults to current directory)",
    ),
]
OutputPrefixOption = Annotated[
    str | None, typer.Option("--prefix", "-n", help="Prefix for exported filenames")
]
SizeFormatOption = Annotated[
    SizeFormat | None,
    typer.Option(
        "--size-format",
        help=(
            f"{HELP_SIZE_FORMAT} Defaults to the project config, then the user config."
        ),
    ),
]
VerboseOption = Annotated[bool, typer.Option("--verbose", "-v", help=HELP_VERBOSE)]


config_app = typer.Typer(help="Manage recursivist user configuration")
app.add_typer(config_app, name="config")


def _without_setting(stored: dict[str, Any], config_key: str) -> dict[str, Any]:
    """Return the stored user configuration without its entries for one key.

    A key may be stored under either spelling (``icon_style`` or a hand-written
    ``icon-style``), so both are dropped. Every other entry is kept as it is, including
    ones recursivist does not recognize.

    Args:
        stored: The user configuration as read from its file.
        config_key: The key to drop, in its underscored form.

    Returns:
        A mapping holding the remaining entries, in their stored order.
    """
    return {
        stored_key: stored_value
        for stored_key, stored_value in stored.items()
        if stored_key.replace("-", "_") != config_key
    }


def _known_config_key(key: str) -> str:
    """Return a recognized configuration key in its stored, underscored form.

    Args:
        key: The key as given on the command line, written with dashes or underscores.

    Returns:
        The key as it appears in `CONFIG_KEYS`.

    Raises:
        typer.Exit: With exit code ``1``, after logging the valid keys, if *key* is not
            a recognized configuration key.
    """
    config_key = key.replace("-", "_")
    if config_key not in CONFIG_KEYS:
        valid_keys = ", ".join(k.replace("_", "-") for k in CONFIG_KEYS)
        logger.error("Unknown configuration key: %s. Valid keys: %s.", key, valid_keys)
        raise typer.Exit(1)
    return config_key


def _quoted(value: str | list[str]) -> str:
    """Return a configuration value for a message, each string in single quotes.

    A list is shown as its quoted strings separated by commas. The quotes keep names
    holding spaces distinguishable.
    """
    strings = value if isinstance(value, list) else [value]
    return ", ".join(f"'{string}'" for string in strings)


@config_app.command("set")
def config_set(
    key: Annotated[
        str,
        typer.Argument(
            help=(
                "Configuration key (icon-style, date-format, size-format, "
                "ignore-file, or exclude)"
            )
        ),
    ],
    value: Annotated[
        list[str],
        typer.Argument(
            help=(
                "Configuration value (e.g., nerd, iso, or .gitignore); "
                "exclude takes one or more directory names"
            ),
        ),
    ],
) -> None:
    """Set a persistent configuration value.

    Saves a user preference to the global configuration file. The keys are
    `icon-style` (`emoji` or `nerd`), `date-format` (`relative` or `iso`, the
    format of modification times), `size-format` (`iec` or `si`, the format
    of file sizes), `ignore-file` (the name of an ignore file to honor, such
    as `.gitignore`), and `exclude` (directory names to exclude). `exclude`
    takes one name per argument and replaces the saved names as a whole;
    every other key takes exactly one value. A project configuration file
    overrides the value saved here.

    Examples:
        >>> recursivist config set icon-style nerd
        >>> recursivist config set date-format iso
        >>> recursivist config set size-format si
        >>> recursivist config set ignore-file .gitignore
        >>> recursivist config set exclude node_modules .git "Application Support"
    """
    config_key = _known_config_key(key)

    setting: str | list[str]
    if config_key in LIST_KEYS:
        setting = list(dict.fromkeys(parse_list_option(value)))
    elif len(value) > 1:
        logger.error(
            "%s takes a single value, but %d were given. "
            "Quote a value that contains spaces.",
            key,
            len(value),
        )
        raise typer.Exit(1)
    else:
        setting = value[0]

    if not accepts_value(config_key, setting):
        logger.error(
            "Invalid value for %s: %s. Use %s.",
            key,
            _quoted(value),
            describe_accepted_values(config_key),
        )
        raise typer.Exit(1)

    config = _without_setting(read_config_file(), config_key)
    config[config_key] = setting
    save_config(config)
    typer.echo(f"Configuration updated: {key} = {_quoted(setting)}")


@config_app.command("unset")
def config_unset(
    key: Annotated[
        str, typer.Argument(help="Configuration key to remove (e.g., icon-style)")
    ],
) -> None:
    """Remove a saved configuration value.

    Deletes one entry from the global configuration file, returning the setting
    to the project configuration or the built-in default. Any key is accepted,
    written with dashes or underscores, including one that recursivist does not
    recognize and reports with a warning. A key that is not saved is not an
    error.

    Examples:
        >>> recursivist config unset icon-style
    """
    stored = read_config_file()
    remaining = _without_setting(stored, key.replace("-", "_"))
    if len(remaining) == len(stored):
        message = f"Nothing to unset: {key} is not saved"
        if stored:
            message += f" (saved keys: {', '.join(stored)})"
        typer.echo(message)
        return

    save_config(remaining)
    typer.echo(f"Configuration updated: {key} unset")


@config_app.command("reset")
def config_reset(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Remove without asking for confirmation"),
    ] = False,
) -> None:
    """Remove every saved configuration value.

    Deletes the global configuration file, so every setting falls back to the
    project configuration or the built-in default. Confirmation is asked for
    first, and declining, or having no answer to read, as in a script, exits
    with code 1; pass `--yes` to skip the question. The removed entries are
    printed with their values. Project configuration files are left as they are.

    Examples:
        >>> recursivist config reset
        >>> recursivist config reset --yes
    """
    config_file = get_config_path()
    if not os.path.isfile(config_file):
        typer.echo("Nothing to reset: no configuration is saved")
        return

    stored = read_config_file()
    entries = ", ".join(f"{key} = {value!r}" for key, value in stored.items())
    if not yes:
        question = (
            f"Remove every saved preference ({entries})?"
            if entries
            else f"Remove the configuration file {config_file}?"
        )
        typer.confirm(question, abort=True)

    try:
        delete_config_file()
    except OSError:
        logger.exception("Could not remove the configuration file")
        raise typer.Exit(1) from None
    typer.echo(
        f"Configuration reset: removed {entries}" if entries else "Configuration reset"
    )


@config_app.command("get")
def config_get(
    key: Annotated[
        str, typer.Argument(help="Configuration key to print (e.g., icon-style)")
    ],
) -> None:
    """Print the value of a user configuration setting.

    Prints the value saved in the global configuration file, or the built-in
    default when the key is not saved or its saved value is invalid. The key may
    be written with dashes or underscores. Only the value is written to standard
    output, one directory name per line for `exclude`, ready for use in a shell
    substitution. Project configuration files are not consulted; `config list`
    shows the value in effect for a directory.

    Examples:
        >>> recursivist config get icon-style
        >>> recursivist config get exclude
        >>> recursivist export --icon-style "$(recursivist config get icon-style)"
    """
    config_key = _known_config_key(key)
    value = resolve_config()[config_key]
    if config_key in LIST_KEYS:
        for item in value or []:
            typer.echo(item)
    else:
        typer.echo(value or "")


_NOT_SET = "(not set)"


def _effective_layer(layers: list[ConfigLayer]) -> ConfigLayer:
    """Return the layer whose value is in effect.

    That is the first layer that sets a value, or the last one, the built-in default,
    when no layer does.
    """
    return next((layer for layer in layers if layer.value is not None), layers[-1])


def _shown_value(layer: ConfigLayer) -> str:
    """Return a layer's value as plain text, ``(not set)`` when it has none.

    The strings of a list value are joined with commas.
    """
    if layer.value is None:
        return _NOT_SET
    if isinstance(layer.value, list):
        return ", ".join(layer.value)
    return layer.value


def _layer_record(layer: ConfigLayer) -> dict[str, Any]:
    """Return one layer's value, name, and source file as JSON-ready fields."""
    return {
        "value": layer.value,
        "layer": layer.name,
        "source": None if layer.source is None else str(layer.source),
    }


def _config_listing_records(
    settings: dict[str, list[ConfigLayer]], show_all: bool
) -> dict[str, dict[str, Any]]:
    """Build the JSON form of a configuration listing.

    Args:
        settings: Each setting's layers in precedence order, keyed by the setting's
            dashed name.
        show_all: Whether to add every layer of a setting under a ``layers`` entry.

    Returns:
        A mapping from each setting to the record of its effective layer, extended with
        the records of all its layers when *show_all* is set.
    """
    records: dict[str, dict[str, Any]] = {}
    for key, layers in settings.items():
        record = _layer_record(_effective_layer(layers))
        if show_all:
            record["layers"] = [_layer_record(layer) for layer in layers]
        records[key] = record
    return records


def _config_listing_lines(
    settings: dict[str, list[ConfigLayer]], show_all: bool
) -> list[str]:
    """Build the plain-text form of a configuration listing.

    Without *show_all* each setting takes one line, ``key = value  (layer: file)``,
    with the file left out for a built-in default. With it, the line holds only the key
    and value and is followed by one indented row per layer: the row of the effective
    layer is marked with ``*``, and a layer without a value shows ``(not set)``. Columns
    are padded to line up across settings.

    Args:
        settings: Each setting's layers in precedence order, keyed by the setting's
            dashed name.
        show_all: Whether to list every layer of a setting instead of only naming the
            effective one.

    Returns:
        The lines of the listing, without line endings.
    """
    effective = {key: _effective_layer(layers) for key, layers in settings.items()}
    if not show_all:
        key_width = max(len(key) for key in effective)
        value_width = max(len(_shown_value(layer)) for layer in effective.values())
        lines = []
        for key, layer in effective.items():
            origin = layer.name
            if layer.source is not None:
                origin += f": {layer.source}"
            value = _shown_value(layer)
            lines.append(f"{key:<{key_width}} = {value:<{value_width}}  ({origin})")
        return lines

    every_layer = [layer for layers in settings.values() for layer in layers]
    name_width = max(len(layer.name) for layer in every_layer)
    value_width = max(len(_shown_value(layer)) for layer in every_layer)
    lines = []
    for key, layers in settings.items():
        lines.append(f"{key} = {_shown_value(effective[key])}")
        for layer in layers:
            marker = "*" if layer is effective[key] else " "
            row = (
                f"  {marker} {layer.name:<{name_width}}  "
                f"{_shown_value(layer):<{value_width}}  {layer.source or ''}"
            )
            lines.append(row.rstrip())
    return lines


@config_app.command("list")
def config_list(
    directory: Annotated[
        str,
        typer.Argument(
            help=(
                "Directory whose project configuration applies "
                "(defaults to current directory)"
            ),
        ),
    ] = ".",
    show_all: Annotated[
        bool,
        typer.Option(
            "--all", "-a", help="Show the value of every layer, not only the winner"
        ),
    ] = False,
    as_json: Annotated[
        bool, typer.Option("--json", help="Print the listing as JSON")
    ] = False,
) -> None:
    """List every configuration setting with the value in effect and its origin.

    Each setting is resolved the way a command run on the directory resolves
    it: the project configuration that applies to the directory, then the
    user configuration file, then the built-in default. The listing names the
    layer and the file each value comes from. `--all` adds the value of every
    layer, marking the winning one with `*`, and `--json` prints the listing
    as JSON. Nothing is created or changed.

    Examples:
        >>> recursivist config list
        >>> recursivist config list /path/to/project --all
        >>> recursivist config list --json
    """
    project_dir = _resolve_and_validate_directory(Path(directory))
    settings = {
        key.replace("_", "-"): layers
        for key, layers in resolve_config_layers(project_dir).items()
    }
    if as_json:
        typer.echo(json.dumps(_config_listing_records(settings, show_all), indent=2))
    else:
        for line in _config_listing_lines(settings, show_all):
            typer.echo(line)


@config_app.command("path")
def config_path() -> None:
    """Print the path of the user configuration file.

    This is the global file that `config set` and `config unset` edit; its
    location follows each platform's convention for application data. The
    path is the only output, and it is printed whether or not the file
    exists.

    Examples:
        >>> recursivist config path
        >>> cat "$(recursivist config path)"
    """
    typer.echo(get_config_path())


def _configure_logging(ctx: typer.Context) -> None:
    """Send the package's log records to the terminal for one CLI invocation.

    Attaches a Rich handler to the ``recursivist`` logger and sets it to INFO, then
    registers a cleanup on ``ctx`` that detaches the handler and restores the previous
    level once the invocation finishes. Logging is therefore configured only while a
    command is running: importing this module configures nothing, the root logger is
    never touched, and a ``--verbose`` run leaves no DEBUG level behind in the process.

    The handler writes to standard error, so that standard output carries only what a
    command prints as its result and can be piped or captured. It shares `err_console`
    with the scanning progress bar, which keeps a record logged during a scan from
    garbling the bar.

    Args:
        ctx: The context of the running application; the logging setup lives exactly as
            long as it does.
    """
    handler = RichHandler(console=err_console, rich_tracebacks=True)
    handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    def restore() -> None:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)

    ctx.call_on_close(restore)


@app.callback()
def callback(ctx: typer.Context) -> None:
    """Recursivist CLI tool for directory visualization and export.

    Entry-point callback invoked by Typer before any subcommand is dispatched. It sets
    up logging for the invocation.
    """
    _configure_logging(ctx)


def parse_list_option(option_value: list[str] | None) -> list[str]:
    """Normalize the raw values collected for a repeatable list option.

    To supply multiple values, repeat the flag once per value:
       >>> --exclude "Application Support" --exclude node_modules

    Each occurrence is preserved verbatim, spaces included. This is required to name
    directories or patterns such as ``"Application Support"`` or ``"My Documents"``;
    those would be impossible to express if values were split on whitespace.

    Each value is stripped of surrounding whitespace, and values that are empty or
    whitespace-only (e.g. from ``--exclude ""``) are dropped. Interior whitespace is
    left untouched.

    Args:
        option_value: Raw list of strings collected by Typer for a repeatable option,
            one element per flag occurrence. Pass ``None`` when the option was not
            provided.

    Returns:
        List of non-empty values with surrounding whitespace trimmed and interior spaces
        preserved. Returns an empty list when *option_value* is ``None`` or holds only
        empty values.

    Examples:
        >>> parse_list_option(["node_modules", ".git", "__pycache__"])
        ['node_modules', '.git', '__pycache__']
        >>> parse_list_option(["Application Support", "My Documents"])
        ['Application Support', 'My Documents']
        >>> parse_list_option(["  spaced  ", "", "   "])
        ['spaced']
        >>> parse_list_option(None)
        []
    """
    if not option_value:
        return []
    result = []
    for item in option_value:
        stripped = item.strip()
        if stripped:
            result.append(stripped)
    return result


def _log_display_options(
    max_depth: int,
    show_full_path: bool,
    spec: DisplayOptions,
) -> None:
    """Log the depth and resolved display/sort options for a command.

    Emits the informational messages shared by the visualize, export, and compare
    commands, driven by the already-resolved
    [`DisplayOptions`][recursivist.flags.DisplayOptions]: the single active sort key (if
    any), each displayed metric in order, and whether Git-status markers are shown. Has
    no effect for options left at their defaults.

    Args:
        max_depth: Maximum directory depth; a message is logged when greater than ``0``.
        show_full_path: Whether full paths are shown.
        spec: The resolved sorting and annotation directives to report.
    """
    if max_depth > 0:
        level_word = "level" if max_depth == 1 else "levels"
        logger.info("Limiting depth to %d %s", max_depth, level_word)
    if show_full_path:
        logger.info(MSG_FULL_PATH)
    if spec.sort_key and spec.sort_key in MSG_SORT_BY:
        logger.info(MSG_SORT_BY[spec.sort_key])
    for metric in spec.metrics:
        if metric in MSG_DISPLAY_METRIC:
            logger.info(MSG_DISPLAY_METRIC[metric])
    if spec.show_git_status:
        logger.info(MSG_GIT_STATUS)


def _parse_filter_options(
    exclude_dirs: list[str] | None,
    exclude_extensions: list[str] | None,
    exclude_patterns: list[str] | None,
    include_patterns: list[str] | None,
    use_regex: bool,
    verbose: bool,
) -> tuple[list[str], set[str], list[str], list[str]]:
    """Parse and normalize the shared exclude/include filter options.

    Normalizes each repeated flag value (dropping empties), lowercases and dot-prefixes
    excluded extensions into a set, rejects invalid ``--regex`` patterns, and emits the
    same debug logging used by every command. This is the common preprocessing step
    shared by the visualize, export, and compare commands.

    Args:
        exclude_dirs: Raw directory-exclusion values from Typer.
        exclude_extensions: Raw extension-exclusion values from Typer.
        exclude_patterns: Raw exclude-pattern values from Typer.
        include_patterns: Raw include-pattern values from Typer.
        use_regex: Whether patterns are regex. When ``True`` every pattern is
            validated here, before any scanning or downloading starts.
        verbose: Whether to log the traceback of an invalid pattern.

    Returns:
        A tuple of ``(parsed_exclude_dirs, exclude_exts_set, parsed_exclude_patterns,
        parsed_include_patterns)``.

    Raises:
        typer.Exit: With exit code ``1`` if *use_regex* is ``True`` and a pattern is
            not a valid regular expression.
    """
    parsed_exclude_dirs = parse_list_option(exclude_dirs)
    parsed_exclude_exts = parse_list_option(exclude_extensions)
    parsed_exclude_patterns = parse_list_option(exclude_patterns)
    parsed_include_patterns = parse_list_option(include_patterns)
    try:
        compile_regex_patterns(
            [*parsed_exclude_patterns, *parsed_include_patterns], use_regex
        )
    except InvalidPatternError as e:
        logger.error(MSG_ERROR, e, exc_info=verbose)
        raise typer.Exit(1) from None
    exclude_exts_set = normalize_extensions(parsed_exclude_exts)
    if exclude_exts_set:
        logger.debug("Excluding extensions: %s", exclude_exts_set)
    if parsed_exclude_dirs:
        logger.debug("Excluding directories: %s", parsed_exclude_dirs)
    if parsed_exclude_patterns:
        pattern_type = "regex" if use_regex else "glob"
        logger.debug("Excluding %s patterns: %s", pattern_type, parsed_exclude_patterns)
    if parsed_include_patterns:
        pattern_type = "regex" if use_regex else "glob"
        logger.debug("Including %s patterns: %s", pattern_type, parsed_include_patterns)
    return (
        parsed_exclude_dirs,
        exclude_exts_set,
        parsed_exclude_patterns,
        parsed_include_patterns,
    )


def _enable_verbose_if_requested(verbose: bool) -> None:
    """Lower the logger to DEBUG when verbose output is requested.

    Shared by the visualize, export, and compare commands as the single definition of
    the verbose preamble. The level lasts only for the current invocation:
    `_configure_logging` restores the previous one when the command finishes.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug(MSG_VERBOSE)


def _resolve_and_validate_directory(directory: Path) -> Path:
    """Resolve a directory path and verify it points at a directory.

    Centralizes the existence/`is_dir` check shared by the visualize and export
    commands, keeping the validation behavior and error message consistent.

    Args:
        directory: Raw directory path as received from Typer.

    Returns:
        The resolved (absolute) directory path.

    Raises:
        typer.Exit: With exit code ``1`` if the resolved path does not exist or is not a
            directory.
    """
    directory = directory.resolve()
    if not directory.is_dir():
        logger.error("Error: %s is not a valid directory", directory)
        raise typer.Exit(1)
    return directory


def _resolve_ignore_file(
    directories: list[Path], ignore_file: str | None
) -> str | None:
    """Resolve the ignore file name, optionally adding a leading dot.

    Checks if the provided ignore_file exists in any of the target directories. If it
    doesn't, but a version with a leading dot does, returns the dotted version.
    Otherwise, returns the original filename for the normal warning logic to handle.

    Args:
        directories: List of resolved directory paths to check for the ignore file.
        ignore_file: Filename of the ignore file to look for, or ``None`` when there is
            none.

    Returns:
        The resolved filename string (potentially with an added dot), or the original
        filename if no dotted version is found. Returns ``None`` if *ignore_file* is
        ``None`` or empty.
    """
    if not ignore_file:
        return None

    if any((d / ignore_file).exists() for d in directories):
        return ignore_file

    if not ignore_file.startswith("."):
        dotted_file = f".{ignore_file}"
        if any((d / dotted_file).exists() for d in directories):
            return dotted_file

    return ignore_file


def _config_reader(project_dir: Path | None) -> Callable[[], dict[str, Any]]:
    """Return a function that gives the configuration in effect for *project_dir*.

    The configuration is resolved on the first call and reused on later ones, so a
    command reads the configuration files at most once, and not at all when
    command-line options settle every setting it would look up. The function takes no
    arguments and returns the mapping of
    [`resolve_config`][recursivist.config.resolve_config]; a *project_dir* of ``None``
    leaves the project layer out.
    """
    return functools.cache(lambda: resolve_config(project_dir))


def _choose_ignore_file(
    directories: list[Path],
    ignore_file: str | None,
    configured: Callable[[], dict[str, Any]],
) -> str | None:
    """Choose the ignore file for a scan of local directories.

    The ``--ignore-file`` option wins whenever it is given, and an empty value there
    means that no ignore file is honored. Without the option, the ``ignore-file``
    configuration setting is used. Either way `_resolve_ignore_file` makes the name's
    leading dot optional.

    *configured* is the function returned by `_config_reader`; it is only called when
    the option was not supplied. The result is ``None`` when no ignore file is honored.
    """
    if ignore_file is None:
        ignore_file = configured().get("ignore_file")
    return _resolve_ignore_file(directories, ignore_file)


def _choose_exclude_dirs(
    exclude_dirs: list[str] | None,
    configured: Callable[[], dict[str, Any]],
) -> list[str] | None:
    """Choose the directories to exclude from a scan.

    The ``--exclude`` option wins whenever it is given: its values are used on their
    own, without the configured ones, and an empty value there means that no directory
    is excluded. Without the option, the ``exclude`` configuration setting is used.

    *configured* is the function returned by `_config_reader`; it is only called when
    the option was not supplied. The names are returned as given, not yet normalized,
    and the result is ``None`` when there are none.
    """
    if exclude_dirs is None:
        return configured().get("exclude")
    return exclude_dirs


def _with_date_format(
    spec: DisplayOptions,
    date_format: DateFormat | None,
    configured: Callable[[], dict[str, Any]] | None,
) -> DisplayOptions:
    """Return *spec* with the format of its modification times chosen.

    The ``--date-format`` option wins whenever it is given. Without it, output shown in
    the terminal uses the ``date-format`` configuration setting, and output written to
    a file uses ``"iso"``: a relative time such as ``Today 14:30`` stops being true once
    the file is read on another day.

    The configuration is only read when the format decides something, that is, when
    *spec* displays modification times.

    Args:
        spec: The resolved sorting and annotation directives.
        date_format: The value of the ``--date-format`` option, or ``None`` when it was
            not given.
        configured: The function returned by `_config_reader` for output shown in the
            terminal, or ``None`` for output written to a file.

    Returns:
        A [`DisplayOptions`][recursivist.flags.DisplayOptions] equal to *spec* except
        for its date format.
    """
    resolved: str
    if date_format is not None:
        resolved = date_format
    elif configured is None:
        resolved = "iso"
    elif spec.show_mtime:
        resolved = configured().get("date_format") or "relative"
    else:
        resolved = "relative"
    return replace(spec, date_format=resolved)


def _with_size_format(
    spec: DisplayOptions,
    size_format: SizeFormat | None,
    configured: Callable[[], dict[str, Any]],
) -> DisplayOptions:
    """Return *spec* with the format of its file sizes chosen.

    The ``--size-format`` option wins whenever it is given. Without it, the
    ``size-format`` configuration setting is used, in the terminal and in output
    written to a file alike: unlike a relative time, a size reads the same wherever and
    whenever it is read.

    The configuration is only read when the format decides something, that is, when
    *spec* displays file sizes.

    Args:
        spec: The resolved sorting and annotation directives.
        size_format: The value of the ``--size-format`` option, or ``None`` when it was
            not given.
        configured: The function returned by `_config_reader`.

    Returns:
        A [`DisplayOptions`][recursivist.flags.DisplayOptions] equal to *spec* except
        for its size format.
    """
    resolved: str
    if size_format is not None:
        resolved = size_format
    elif spec.show_size:
        resolved = configured().get("size_format") or "iec"
    else:
        resolved = "iec"
    return replace(spec, size_format=resolved)


def _warn_if_ignore_file_missing(
    directory: Path, ignore_file: str | None, *, configured: bool = False
) -> None:
    """Log whether the ignore file in use exists inside *directory*.

    Emits a debug message when the ignore file is found. When it is absent, a file named
    with ``--ignore-file`` is reported with a warning, since it was asked for on this
    run. One that comes from the configuration is a standing preference that applies
    wherever the file exists, and its absence is only a debug message. Does nothing when
    no ignore file is in use. Shared by the visualize and export commands.

    Args:
        directory: Directory in which to look for the ignore file.
        ignore_file: Filename of the ignore file to look for, or ``None`` when there is
            none.
        configured: Whether the filename comes from the configuration rather than from
            the ``--ignore-file`` option.
    """
    if not ignore_file:
        return
    ignore_path = directory / ignore_file
    if ignore_path.exists():
        logger.debug("Using ignore file: %s", ignore_path)
    elif configured:
        logger.debug("Configured ignore file not found: %s", ignore_path)
    else:
        logger.warning("Ignore file not found: %s", ignore_path)


def _compile_patterns_for_scan(
    parsed_exclude_patterns: list[str],
    parsed_include_patterns: list[str],
    use_regex: bool,
) -> tuple[list[str | Pattern[str]], list[str | Pattern[str]]]:
    """Compile exclude/include patterns for the scanner.

    When *use_regex* is ``True`` the patterns are compiled to regular expressions;
    otherwise [`compile_regex_patterns`][recursivist.filtering.compile_regex_patterns]
    passes the plain glob strings through unchanged. Shared by the visualize and export
    commands.

    Args:
        parsed_exclude_patterns: Flat list of exclude-pattern strings.
        parsed_include_patterns: Flat list of include-pattern strings.
        use_regex: Whether the patterns should be treated as regex.

    Returns:
        A ``(compiled_exclude, compiled_include)`` tuple suitable for passing directly
        to [`get_directory_structure`][recursivist.scanner.get_directory_structure].
    """
    return (
        compile_regex_patterns(parsed_exclude_patterns, use_regex),
        compile_regex_patterns(parsed_include_patterns, use_regex),
    )


def _scan_directory(
    directory: Path,
    parsed_exclude_dirs: list[str],
    ignore_file: str | None,
    exclude_exts_set: set[str],
    parsed_exclude_patterns: list[str],
    parsed_include_patterns: list[str],
    use_regex: bool,
    max_depth: int,
    show_full_path: bool,
    collect_loc: bool,
    collect_size: bool,
    collect_mtime: bool,
    show_git_status: bool,
) -> tuple[Directory, set[str]]:
    """Fetch Git status and scan *directory* into a tree structure.

    Encapsulates the scanning pipeline shared by the visualize and export commands:
    optionally resolving the Git status map, compiling patterns, running the scan under
    a progress indicator, and logging the number of unique extensions found. When Git
    status cannot be read, a warning naming the cause is logged and the scan proceeds
    without it.

    Args:
        directory: Resolved directory to scan.
        parsed_exclude_dirs: Directory names to exclude.
        ignore_file: Ignore filename to honor, or ``None``.
        exclude_exts_set: Normalized set of excluded extensions.
        parsed_exclude_patterns: Flat list of exclude patterns.
        parsed_include_patterns: Flat list of include patterns.
        use_regex: Whether patterns are regular expressions.
        max_depth: Maximum directory depth (``0`` for unlimited).
        show_full_path: Whether full paths are requested.
        collect_loc: Whether to compute lines-of-code counts.
        collect_size: Whether to compute file sizes.
        collect_mtime: Whether to compute modification times.
        show_git_status: Whether to annotate files with Git status.

    Returns:
        A ``(structure, extensions)`` tuple as produced by
        [`get_directory_structure`][recursivist.scanner.get_directory_structure].
    """
    git_status_map: dict[str, str] | None = None
    if show_git_status:
        try:
            git_status_map = get_git_status(str(directory))
        except GitStatusError as e:
            logger.warning("Git status unavailable for %s: %s", directory, e)
    with Progress(console=err_console) as progress:
        progress.add_task("[cyan]Scanning directory structure...", total=None)
        compiled_exclude, compiled_include = _compile_patterns_for_scan(
            parsed_exclude_patterns,
            parsed_include_patterns,
            use_regex,
        )
        structure, extensions = get_directory_structure(
            str(directory),
            exclude_dirs=parsed_exclude_dirs,
            ignore_file=ignore_file,
            exclude_extensions=exclude_exts_set,
            exclude_patterns=compiled_exclude,
            include_patterns=compiled_include,
            max_depth=max_depth,
            show_full_path=show_full_path,
            collect_loc=collect_loc,
            collect_size=collect_size,
            collect_mtime=collect_mtime,
            git_status_map=git_status_map,
        )
        logger.debug("Found %d unique file extensions", len(extensions))
    return structure, extensions


def _log_ignored_remote_flags(
    ignore_file: str | None,
    sort_by_git_status: bool,
    show_git_status: bool,
    sort_by_mtime: bool,
    show_mtime: bool,
) -> None:
    """Report which options are being skipped for a GitHub input.

    The ``--ignore-file``, ``--git-status``, ``--sort-by-git-status``, ``--mtime`` and
    ``--sort-by-mtime`` options are not meaningful for a hosted repository (see
    [`recursivist.github`][recursivist.github]); when any were supplied for a GitHub
    input, this logs an informational message naming them rather than dropping them
    silently.

    Args:
        ignore_file: The requested ignore filename, if any.
        sort_by_git_status: Whether ``--sort-by-git-status`` was given.
        show_git_status: Whether ``--git-status`` was given.
        sort_by_mtime: Whether ``--sort-by-mtime`` was given.
        show_mtime: Whether ``--mtime`` was given.
    """
    ignored: list[str] = []
    if ignore_file:
        ignored.append("--ignore-file")
    if sort_by_git_status:
        ignored.append("--sort-by-git-status")
    if show_git_status:
        ignored.append("--git-status")
    if sort_by_mtime:
        ignored.append("--sort-by-mtime")
    if show_mtime:
        ignored.append("--mtime")
    if ignored:
        logger.info(
            "Ignoring %s for GitHub repository (not applicable to hosted repositories)",
            ", ".join(ignored),
        )


def _compare_inputs_are_same(
    dir1: str,
    dir2: str,
    target1: GitHubTarget | None,
    target2: GitHubTarget | None,
) -> bool:
    """Return whether both ``compare`` inputs refer to the same target.

    Comparing a structure against itself produces a diff in which every item is shared
    and nothing is unique, which is never what the caller intends. The `compare` command
    uses this to reject that case instead of doing pointless work.

    The two inputs are considered the same when:

    * both are GitHub repositories that resolve to the same repository, ref and subtree
      — see [`same_github_target`][recursivist.github.same_github_target] for how
      owner/repo case-insensitivity and the default branch are handled; or
    * both are local directories whose resolved absolute paths are equal. This covers
      ``dir`` and ``dir/``, relative and absolute spellings, and symlinks pointing at
      the same location.

    A local directory and a GitHub repository are never the same.

    Args:
        dir1: The first raw input as given on the command line.
        dir2: The second raw input as given on the command line.
        target1: The parsed GitHub target for *dir1*, or ``None`` if it is a local path.
        target2: The parsed GitHub target for *dir2*, or ``None`` if it is a local path.

    Returns:
        ``True`` if the two inputs refer to the same target, else ``False``.
    """
    if target1 is not None and target2 is not None:
        return same_github_target(target1, target2, get_github_token())
    if target1 is None and target2 is None:
        try:
            return Path(dir1).resolve() == Path(dir2).resolve()
        except OSError:
            return Path(dir1).absolute() == Path(dir2).absolute()
    return False


@dataclass(frozen=True)
class _TreeScanPlan:
    """How the visualize or export command is to scan its input, fully resolved.

    Built by `_plan_tree_scan` and consumed by `_scanned_tree`.

    Attributes:
        target: The parsed GitHub target, or ``None`` for a local directory.
        directory: The resolved local directory to scan. Only meaningful when *target*
            is ``None``.
        ignore_file: Ignore filename to honor, or ``None``. Always ``None`` for a GitHub
            input.
        ignore_file_configured: Whether *ignore_file* comes from the configuration
            rather than from the ``--ignore-file`` option.
        spec: The resolved sorting and annotation directives.
        icon_style: The icon style to render with.
        exclude_dirs: Parsed directory names to exclude.
        exclude_extensions: Normalized set of excluded extensions.
        exclude_patterns: Parsed exclude patterns.
        include_patterns: Parsed include patterns.
        use_regex: Whether the patterns are regular expressions.
        max_depth: Maximum directory depth (``0`` for unlimited).
        show_full_path: Whether full paths are requested.
    """

    target: GitHubTarget | None
    directory: Path
    ignore_file: str | None
    ignore_file_configured: bool
    spec: DisplayOptions
    icon_style: str
    exclude_dirs: list[str]
    exclude_extensions: set[str]
    exclude_patterns: list[str]
    include_patterns: list[str]
    use_regex: bool
    max_depth: int
    show_full_path: bool


@dataclass(frozen=True)
class _ScannedTree:
    """A scanned input, as yielded by `_scanned_tree`.

    Attributes:
        root_name: Display name for the root of the tree.
        structure: The scanned structure, with file paths already rewritten to GitHub
            blob URLs when full paths were requested for a GitHub input.
        extensions: The file extensions found by the scan.
    """

    root_name: str
    structure: Directory
    extensions: set[str]


def _plan_tree_scan(
    ctx: typer.Context,
    directory: str,
    *,
    exclude_dirs: list[str] | None,
    exclude_extensions: list[str] | None,
    exclude_patterns: list[str] | None,
    include_patterns: list[str] | None,
    use_regex: bool,
    ignore_file: str | None,
    max_depth: int,
    show_full_path: bool,
    sort_by_loc: bool,
    sort_by_size: bool,
    sort_by_mtime: bool,
    sort_by_git_status: bool,
    sort_by_similarity: bool,
    loc: bool,
    size: bool,
    mtime: bool,
    show_git_status: bool,
    icon_style: IconStyle | None,
    date_format: DateFormat | None,
    size_format: SizeFormat | None,
    verbose: bool,
    use_configured_icon_style: bool,
    use_configured_date_format: bool,
) -> _TreeScanPlan:
    """Resolve the options shared by visualize and export into a scan plan.

    Runs the option handling both commands have in common, in the order its messages
    are logged: recognizing a GitHub input, resolving the sorting and annotation flags,
    validating a local directory, choosing the ignore file, the icon style and the date
    and size formats, logging the display options, and parsing the filters. For a
    GitHub input the options that do not apply to a hosted repository are dropped, and
    reported when they were given.

    Apart from the three below, the arguments are the command options of the same name,
    as received from Typer and documented on `visualize`.

    Args:
        ctx: The command's Typer context, giving the order the flags were written in.
        use_configured_icon_style: Whether the ``icon_style`` configuration setting
            applies when *icon_style* is ``None``. When ``False`` the style falls back
            to ``"emoji"`` regardless of the configuration.
        use_configured_date_format: Whether the ``date_format`` configuration setting
            applies when *date_format* is ``None``. When ``False`` the format falls back
            to ``"iso"`` regardless of the configuration.

    Returns:
        The resolved plan.

    Raises:
        typer.Exit: With exit code ``1`` if *directory* is a local path that does not
            exist or is not a directory, or if *use_regex* is ``True`` and a pattern is
            not a valid regular expression.
    """
    target = parse_github_url(directory)
    is_remote = target is not None

    spec = resolve_display_options(
        sort_loc=sort_by_loc,
        sort_size=sort_by_size,
        sort_mtime=sort_by_mtime and not is_remote,
        sort_similarity=sort_by_similarity,
        sort_git=sort_by_git_status and not is_remote,
        disp_loc=loc,
        disp_size=size,
        disp_mtime=mtime and not is_remote,
        disp_git=show_git_status and not is_remote,
        order=_flag_order(ctx),
    )

    validated: Path = Path(directory)
    if not is_remote:
        validated = _resolve_and_validate_directory(Path(directory))
    configured = _config_reader(None if is_remote else validated)

    ignore_file_configured = ignore_file is None
    if is_remote:
        _log_ignored_remote_flags(
            ignore_file, sort_by_git_status, show_git_status, sort_by_mtime, mtime
        )
        ignore_file = None
    else:
        ignore_file = _choose_ignore_file([validated], ignore_file, configured)

    resolved_style: str = icon_style or (
        configured().get("icon_style", "emoji")
        if use_configured_icon_style
        else "emoji"
    )
    spec = _with_date_format(
        spec,
        date_format,
        configured if use_configured_date_format else None,
    )
    spec = _with_size_format(spec, size_format, configured)

    _log_display_options(max_depth, show_full_path, spec)
    dirs, extensions, excludes, includes = _parse_filter_options(
        _choose_exclude_dirs(exclude_dirs, configured),
        exclude_extensions,
        exclude_patterns,
        include_patterns,
        use_regex,
        verbose,
    )
    return _TreeScanPlan(
        target=target,
        directory=validated,
        ignore_file=ignore_file,
        ignore_file_configured=ignore_file_configured,
        spec=spec,
        icon_style=resolved_style,
        exclude_dirs=dirs,
        exclude_extensions=extensions,
        exclude_patterns=excludes,
        include_patterns=includes,
        use_regex=use_regex,
        max_depth=max_depth,
        show_full_path=show_full_path,
    )


@contextlib.contextmanager
def _scanned_tree(plan: _TreeScanPlan) -> Generator[_ScannedTree]:
    """Scan the input described by *plan* and yield the result.

    A local directory is scanned in place, after reporting whether its ignore file
    exists. A GitHub repository is downloaded and scanned from a temporary checkout,
    which is removed when the ``with`` block exits.

    Args:
        plan: The resolved plan, as returned by `_plan_tree_scan`.

    Yields:
        The scanned structure with what is needed to render it.
    """
    with contextlib.ExitStack() as stack:
        if plan.target is not None:
            checkout = stack.enter_context(checkout_repository(plan.target))
            scan_dir = checkout.local_root
            root_name = checkout.root_name
        else:
            checkout = None
            scan_dir = str(plan.directory)
            root_name = os.path.basename(scan_dir)
            _warn_if_ignore_file_missing(
                Path(scan_dir),
                plan.ignore_file,
                configured=plan.ignore_file_configured,
            )
        structure, extensions = _scan_directory(
            Path(scan_dir),
            plan.exclude_dirs,
            plan.ignore_file,
            plan.exclude_extensions,
            plan.exclude_patterns,
            plan.include_patterns,
            plan.use_regex,
            plan.max_depth,
            plan.show_full_path,
            plan.spec.show_loc,
            plan.spec.show_size,
            plan.spec.show_mtime,
            plan.spec.show_git_status,
        )
        if checkout is not None and plan.show_full_path:
            apply_github_urls(structure, checkout)
        yield _ScannedTree(root_name, structure, extensions)


@app.command()
def visualize(
    ctx: typer.Context,
    directory: Annotated[
        str,
        typer.Argument(
            help=(
                "Directory path or GitHub repository URL to visualize "
                "(defaults to current directory)"
            ),
        ),
    ] = ".",
    exclude_dirs: ExcludeDirsOption = None,
    exclude_extensions: ExcludeExtensionsOption = None,
    exclude_patterns: ExcludePatternsOption = None,
    include_patterns: IncludePatternsOption = None,
    use_regex: UseRegexOption = False,
    ignore_file: IgnoreFileOption = None,
    max_depth: MaxDepthDisplayOption = 0,
    show_full_path: ShowFullPathOption = False,
    sort_by_loc: SortByLocOption = False,
    sort_by_size: SortBySizeOption = False,
    sort_by_mtime: SortByMtimeOption = False,
    sort_by_git_status: SortByGitStatusOption = False,
    sort_by_similarity: SortBySimilarityOption = False,
    loc: LocOption = False,
    size: SizeOption = False,
    mtime: MtimeOption = False,
    show_git_status: ShowGitStatusOption = False,
    icon_style: Annotated[
        IconStyle | None,
        typer.Option(
            "--icon-style",
            help=(
                "Override icon style ('emoji' or 'nerd'). Defaults to the project "
                "config, then the user config."
            ),
        ),
    ] = None,
    date_format: Annotated[
        DateFormat | None,
        typer.Option(
            "--date-format",
            help=(
                f"{HELP_DATE_FORMAT} Defaults to the project config, then the user "
                "config."
            ),
        ),
    ] = None,
    size_format: SizeFormatOption = None,
    verbose: VerboseOption = False,
) -> None:
    """Visualize a directory structure as a tree in the terminal.

    Scans the directory and renders a color-coded tree, optionally annotated
    with lines of code, sizes, modification times, and Git status. The
    directory may also be a GitHub repository URL, which is downloaded and
    scanned like a local directory; options that need a local checkout
    (`--ignore-file`, `--git-status`, `--mtime` and their sorting forms) are
    skipped for it.

    Only the first `--sort-by-*` flag on the command line takes effect, while
    every display flag (`--loc`, `--size`, `--mtime`, `--git-status`)
    annotates, in the order given. Modification times are written in the
    `relative` form unless `--date-format iso` or the `date-format` setting
    asks for ISO 8601 in UTC. File sizes are written in IEC units unless
    `--size-format si` or the `size-format` setting asks for SI units.

    Examples:
        >>> recursivist visualize
        >>> recursivist visualize /path/to/project -e node_modules -e .git
        >>> recursivist visualize -p "*.test.js" -d 2
        >>> recursivist visualize --sort-by-loc --size
        >>> recursivist visualize --mtime --date-format iso
        >>> recursivist visualize --size --size-format si
        >>> recursivist visualize https://github.com/owner/repo/tree/main/src
    """
    _enable_verbose_if_requested(verbose)

    plan = _plan_tree_scan(
        ctx,
        directory,
        exclude_dirs=exclude_dirs,
        exclude_extensions=exclude_extensions,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
        use_regex=use_regex,
        ignore_file=ignore_file,
        max_depth=max_depth,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
        sort_by_git_status=sort_by_git_status,
        sort_by_similarity=sort_by_similarity,
        loc=loc,
        size=size,
        mtime=mtime,
        show_git_status=show_git_status,
        icon_style=icon_style,
        date_format=date_format,
        size_format=size_format,
        verbose=verbose,
        use_configured_icon_style=True,
        use_configured_date_format=True,
    )
    try:
        with _scanned_tree(plan) as scanned:
            logger.info("Displaying directory tree:")
            display_tree(
                scanned.structure,
                scanned.extensions,
                scanned.root_name,
                spec=plan.spec,
                icon_style=plan.icon_style,
            )
    except Exception as e:
        logger.error(MSG_ERROR, e, exc_info=verbose)
        raise typer.Exit(1) from None


@app.command()
def export(
    ctx: typer.Context,
    directory: Annotated[
        str,
        typer.Argument(
            help=(
                "Directory path or GitHub repository URL to export "
                "(defaults to current directory)"
            ),
        ),
    ] = ".",
    formats: Annotated[
        list[str] | None,
        typer.Option(
            "--format",
            "-f",
            show_default="md",
            help="Export formats: txt, json, html, md, svg, rst",
        ),
    ] = None,
    output_dir: OutputDirOption = None,
    output_prefix: OutputPrefixOption = "structure",
    exclude_dirs: ExcludeDirsOption = None,
    exclude_extensions: ExcludeExtensionsOption = None,
    exclude_patterns: ExcludePatternsOption = None,
    include_patterns: IncludePatternsOption = None,
    use_regex: UseRegexOption = False,
    ignore_file: IgnoreFileOption = None,
    max_depth: Annotated[
        int,
        typer.Option("--depth", "-d", help="Maximum depth to export (0 for unlimited)"),
    ] = 0,
    show_full_path: ShowFullPathOption = False,
    sort_by_loc: SortByLocOption = False,
    sort_by_size: SortBySizeOption = False,
    sort_by_mtime: SortByMtimeOption = False,
    sort_by_git_status: SortByGitStatusOption = False,
    sort_by_similarity: SortBySimilarityOption = False,
    loc: LocOption = False,
    size: SizeOption = False,
    mtime: MtimeOption = False,
    show_git_status: ShowGitStatusOption = False,
    icon_style: Annotated[
        IconStyle | None,
        typer.Option(
            "--icon-style",
            help="Override icon style. Defaults to 'emoji' for safe file exports.",
        ),
    ] = None,
    date_format: Annotated[
        DateFormat | None,
        typer.Option(
            "--date-format",
            help=(
                f"{HELP_DATE_FORMAT} Defaults to 'iso', which stays accurate after "
                "the file is written."
            ),
        ),
    ] = None,
    size_format: SizeFormatOption = None,
    verbose: VerboseOption = False,
) -> None:
    """Export a directory structure to one or more file formats.

    Scans the directory and writes one file per requested format, named
    `<prefix>.<format>`, to the output directory, without printing the tree.
    Exports use the `emoji` icon style unless `--icon-style` is given. The
    directory may also be a GitHub repository URL, which is downloaded and
    scanned like a local directory; options that need a local checkout
    (`--ignore-file`, `--git-status`, `--mtime` and their sorting forms) are
    skipped for it.

    Only the first `--sort-by-*` flag on the command line takes effect, while
    every display flag (`--loc`, `--size`, `--mtime`, `--git-status`)
    annotates, in the order given. Exports write modification times as ISO
    8601 in UTC unless `--date-format relative` is given. File sizes are
    written in IEC units unless `--size-format si` or the `size-format`
    setting asks for SI units.

    Examples:
        >>> recursivist export
        >>> recursivist export /path/to/project -f html -o ./exports
        >>> recursivist export -f "json md html"
        >>> recursivist export -f md --mtime --date-format relative
        >>> recursivist export -f md --size --size-format si
        >>> recursivist export https://github.com/owner/repo -f md -l
    """
    _enable_verbose_if_requested(verbose)

    parsed_formats: list[str] = []
    for fmt in formats or ["md"]:
        parsed_formats.extend([x.strip() for x in fmt.split(" ") if x.strip()])
    valid_formats = supported_formats()
    invalid_formats = [
        fmt for fmt in parsed_formats if fmt.lower() not in valid_formats
    ]
    if invalid_formats:
        logger.error("Unsupported export format(s): %s", ", ".join(invalid_formats))
        logger.info("Supported formats: %s", ", ".join(valid_formats))
        raise typer.Exit(1)

    plan = _plan_tree_scan(
        ctx,
        directory,
        exclude_dirs=exclude_dirs,
        exclude_extensions=exclude_extensions,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
        use_regex=use_regex,
        ignore_file=ignore_file,
        max_depth=max_depth,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
        sort_by_git_status=sort_by_git_status,
        sort_by_similarity=sort_by_similarity,
        loc=loc,
        size=size,
        mtime=mtime,
        show_git_status=show_git_status,
        icon_style=icon_style,
        date_format=date_format,
        size_format=size_format,
        verbose=verbose,
        use_configured_icon_style=False,
        use_configured_date_format=False,
    )
    failed_formats: list[str] = []
    try:
        with _scanned_tree(plan) as scanned:
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(".")

            num_formats = len(parsed_formats)
            format_word = "format" if num_formats == 1 else "formats"
            logger.info("Exporting to %d %s", num_formats, format_word)
            for fmt in parsed_formats:
                output_path = output_dir / f"{output_prefix}.{canonical_extension(fmt)}"
                try:
                    exporter = get_exporter(
                        format_type=fmt.lower(),
                        structure=scanned.structure,
                        root_name=scanned.root_name,
                        show_full_path=show_full_path,
                        spec=plan.spec,
                        icon_style=plan.icon_style,
                    )
                    exporter.export(str(output_path))
                    logger.info("Successfully exported to %s", output_path)
                except Exception as e:
                    logger.error("Failed to export to %s: %s", fmt, e, exc_info=verbose)
                    failed_formats.append(fmt)
    except Exception as e:
        logger.error(MSG_ERROR, e, exc_info=verbose)
        raise typer.Exit(1) from None
    if failed_formats:
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Display the current version of recursivist."""
    from recursivist import __version__

    typer.echo(f"Recursivist version: {__version__}")


@app.command()
def compare(
    ctx: typer.Context,
    dir1: Annotated[
        str,
        typer.Argument(help="First directory path or GitHub repository URL to compare"),
    ],
    dir2: Annotated[
        str,
        typer.Argument(
            help="Second directory path or GitHub repository URL to compare"
        ),
    ],
    exclude_dirs: ExcludeDirsOption = None,
    exclude_extensions: ExcludeExtensionsOption = None,
    exclude_patterns: ExcludePatternsOption = None,
    include_patterns: IncludePatternsOption = None,
    use_regex: UseRegexOption = False,
    ignore_file: IgnoreFileOption = None,
    max_depth: MaxDepthDisplayOption = 0,
    save_as_html: Annotated[
        bool,
        typer.Option(
            "--save",
            "-f",
            help="Save comparison as HTML file instead of displaying in terminal",
        ),
    ] = False,
    output_dir: OutputDirOption = None,
    output_prefix: OutputPrefixOption = "comparison",
    show_full_path: ShowFullPathOption = False,
    sort_by_loc: SortByLocOption = False,
    sort_by_size: SortBySizeOption = False,
    sort_by_mtime: SortByMtimeOption = False,
    sort_by_git_status: SortByGitStatusOption = False,
    sort_by_similarity: SortBySimilarityOption = False,
    loc: LocOption = False,
    size: SizeOption = False,
    mtime: MtimeOption = False,
    show_git_status: ShowGitStatusOption = False,
    icon_style: Annotated[
        IconStyle | None,
        typer.Option(
            "--icon-style",
            help=(
                "Override icon style. Defaults to 'emoji' if saving to HTML, "
                "else the project config, then the user config."
            ),
        ),
    ] = None,
    date_format: Annotated[
        DateFormat | None,
        typer.Option(
            "--date-format",
            help=(
                f"{HELP_DATE_FORMAT} Defaults to 'iso' if saving to HTML, else the "
                "project config, then the user config."
            ),
        ),
    ] = None,
    size_format: SizeFormatOption = None,
    verbose: VerboseOption = False,
) -> None:
    """Compare two directory structures side by side.

    Builds the tree of each input with the same filtering options and shows
    the two next to each other, highlighting the items found on one side
    only; a legend explains the colors. With `--save`, the comparison is
    written to an HTML file instead. Either input may be a local directory or
    a GitHub repository URL; `--ignore-file`, `--git-status` and `--mtime`
    are skipped for a GitHub side, and `--sort-by-git-status` and
    `--sort-by-mtime` whenever either side is one.

    Only the first `--sort-by-*` flag on the command line takes effect, while
    every display flag (`--loc`, `--size`, `--mtime`, `--git-status`)
    annotates, in the order given. Modification times are written in the
    `relative` form in the terminal and as ISO 8601 in UTC in a saved HTML
    file; `--date-format` chooses either for a run. File sizes are written
    in IEC units unless `--size-format si` or the `size-format` setting asks
    for SI units.

    Examples:
        >>> recursivist compare dir1 dir2
        >>> recursivist compare dir1 dir2 -e node_modules -d 2
        >>> recursivist compare dir1 dir2 --save -o ./reports
        >>> recursivist compare ./my-fork https://github.com/owner/repo
    """
    _enable_verbose_if_requested(verbose)

    display_dir1 = Path(dir1).resolve().name if dir1 == "." else dir1
    display_dir2 = Path(dir2).resolve().name if dir2 == "." else dir2

    logger.info("Comparing: %s and %s", display_dir1, display_dir2)

    target1 = parse_github_url(dir1)
    target2 = parse_github_url(dir2)
    remote1 = target1 is not None
    remote2 = target2 is not None
    both_remote = remote1 and remote2
    any_remote = remote1 or remote2

    local_inputs = [
        raw for raw, is_remote in ((dir1, remote1), (dir2, remote2)) if not is_remote
    ]
    for raw in local_inputs:
        local_dir = Path(raw)
        if not local_dir.is_dir():
            logger.error("Error: %s is not a valid directory or GitHub URL", raw)
            raise typer.Exit(1)

    if _compare_inputs_are_same(dir1, dir2, target1, target2):
        logger.error(
            "Error: cannot compare %s with itself; "
            "please provide two different directories or repositories",
            display_dir1,
        )
        raise typer.Exit(1)

    local_paths = [Path(raw) for raw in local_inputs]
    configured = _config_reader(local_paths[0] if local_paths else None)

    spec = resolve_display_options(
        sort_loc=sort_by_loc,
        sort_size=sort_by_size,
        sort_mtime=sort_by_mtime and not any_remote,
        sort_similarity=sort_by_similarity,
        sort_git=sort_by_git_status and not any_remote,
        disp_loc=loc,
        disp_size=size,
        disp_mtime=mtime and not both_remote,
        disp_git=show_git_status and not both_remote,
        order=_flag_order(ctx),
    )

    ignore_file_configured = ignore_file is None
    if both_remote:
        _log_ignored_remote_flags(
            ignore_file, sort_by_git_status, show_git_status, sort_by_mtime, mtime
        )
        ignore_file = None
    elif any_remote:
        if ignore_file or show_git_status or mtime:
            logger.info(
                "Ignoring --ignore-file, --git-status and --mtime for the GitHub "
                "repository; they still apply to the local directory"
            )
        if sort_by_git_status or sort_by_mtime:
            logger.info(
                "Ignoring --sort-by-git-status and --sort-by-mtime entirely: both "
                "sides of a comparison share one ordering, and a GitHub repository "
                "has no per-file Git status or modification time to sort on"
            )

    if local_paths:
        ignore_file = _choose_ignore_file(local_paths, ignore_file, configured)

    spec = _with_date_format(spec, date_format, None if save_as_html else configured)
    spec = _with_size_format(spec, size_format, configured)

    _log_display_options(max_depth, show_full_path, spec)

    if icon_style:
        resolved_style = icon_style
    elif save_as_html:
        resolved_style = "emoji"
    else:
        resolved_style = configured().get("icon_style", "emoji")

    (
        parsed_exclude_dirs,
        exclude_exts_set,
        parsed_exclude_patterns,
        parsed_include_patterns,
    ) = _parse_filter_options(
        _choose_exclude_dirs(exclude_dirs, configured),
        exclude_extensions,
        exclude_patterns,
        include_patterns,
        use_regex,
        verbose,
    )
    if ignore_file:
        for d in local_paths:
            ignore_path = d / ignore_file
            if ignore_path.exists():
                logger.debug("Using ignore file from %s: %s", d, ignore_path)
            elif ignore_file_configured:
                logger.debug(
                    "Configured ignore file not found in %s: %s", d, ignore_path
                )
            else:
                logger.warning("Ignore file not found in %s: %s", d, ignore_path)
    try:
        if save_as_html:
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(".")
            output_path = output_dir / f"{output_prefix}.html"
            export_comparison(
                dir1,
                dir2,
                "html",
                str(output_path),
                parsed_exclude_dirs,
                ignore_file,
                exclude_exts_set,
                exclude_patterns=parsed_exclude_patterns,
                include_patterns=parsed_include_patterns,
                use_regex=use_regex,
                max_depth=max_depth,
                show_full_path=show_full_path,
                spec=spec,
                icon_style=resolved_style,
                targets=(target1, target2),
            )
            logger.info("Successfully exported to %s", output_path)
        else:
            display_comparison(
                dir1,
                dir2,
                parsed_exclude_dirs,
                ignore_file,
                exclude_exts_set,
                exclude_patterns=parsed_exclude_patterns,
                include_patterns=parsed_include_patterns,
                use_regex=use_regex,
                max_depth=max_depth,
                show_full_path=show_full_path,
                spec=spec,
                icon_style=resolved_style,
                targets=(target1, target2),
            )
    except Exception as e:
        logger.error(MSG_ERROR, e, exc_info=verbose)
        raise typer.Exit(1) from None


def main() -> None:
    """Entry point for the recursivist CLI application.

    Invokes the Typer application, which parses command-line arguments and dispatches to
    the appropriate subcommand function. This function is registered as the
    ``recursivist`` console-script entry point in the package configuration, along with
    the shorter ``rcv`` alias.
    """
    app()


if __name__ == "__main__":
    main()
