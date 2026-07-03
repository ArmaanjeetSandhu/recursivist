#!/usr/bin/env python3
"""Recursivist CLI - A beautiful directory structure visualization tool.

Provides the command-line interface for the recursivist package, letting
users visualize directory structures, export them in various formats,
compare two structures side-by-side, manage user configurations, and
generate shell completion scripts.

Main commands:
    visualize: Display a directory structure in the terminal with rich
        formatting and optional statistics.
    export: Export a directory structure to TXT, JSON, HTML, MD, JSX,
        SVG, or RST.
    compare: Compare two directory structures with highlighted
        differences.
    config: Manage persistent user preferences like icon styles.
    version: Display the current version information.
    completion: Generate shell completion scripts for various shells.

All commands share a consistent set of filtering and display options:
    - Exclude directories, file extensions, glob, or regex patterns.
    - Include specific patterns that override exclusions.
    - Support for .gitignore and similar ignore files.
    - Depth limitation for large directories.
    - Full-path display option.
    - File statistics with sorting by lines of code, size, or
      modification time.
"""

import logging
import os
import sys
from pathlib import Path
from re import Pattern
from typing import Any, cast

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from recursivist.compare import (
    display_comparison,
    export_comparison,
)
from recursivist.config import load_config, save_config
from recursivist.exporters import get_exporter
from recursivist.filtering import compile_regex_patterns
from recursivist.git_status import get_git_status
from recursivist.scanner import get_directory_structure
from recursivist.tree import display_tree

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("recursivist")
app = typer.Typer(
    help="Recursivist: A beautiful directory structure visualization tool",
    add_completion=True,
)
console = Console()

USER_CONFIG = load_config()

HELP_EXCLUDE_DIRS = "Directories to exclude (space-separated or multiple flags)"
HELP_EXCLUDE_EXTS = "File extensions to exclude (space-separated or multiple flags)"
HELP_EXCLUDE_PATTERNS = "Patterns to exclude (space-separated or multiple flags)"
HELP_INCLUDE_PATTERNS = (
    "Patterns to include (overrides exclusions, space-separated or multiple flags)"
)
HELP_USE_REGEX = "Treat patterns as regex instead of glob patterns"
HELP_IGNORE_FILE = "Ignore file to use (e.g., .gitignore)"
HELP_SHOW_FULL_PATH = "Show full paths instead of just filenames"
HELP_SORT_BY_LOC = "Sort files by lines of code and display LOC counts"
HELP_SORT_BY_SIZE = "Sort files by size and display file sizes"
HELP_SORT_BY_MTIME = "Sort files by modification time and display timestamps"
HELP_SORT_BY_SIMILARITY = (
    "Group files with similar names together (overridden by other sort options)"
)
HELP_VERBOSE = "Enable verbose output"

MSG_VERBOSE = "Verbose mode enabled"
MSG_FULL_PATH = "Showing full paths instead of just filenames"
MSG_SORT_LOC = "Sorting files by lines of code and displaying LOC counts"
MSG_SORT_SIZE = "Sorting files by size and displaying file sizes"
MSG_SORT_MTIME = "Sorting files by modification time and displaying timestamps"
MSG_SORT_SIMILARITY = "Grouping files by name similarity"


def _exclude_dirs_option() -> Any:
    return typer.Option(None, "--exclude", "-e", help=HELP_EXCLUDE_DIRS)


def _exclude_extensions_option() -> Any:
    return typer.Option(None, "--exclude-ext", "-x", help=HELP_EXCLUDE_EXTS)


def _exclude_patterns_option() -> Any:
    return typer.Option(None, "--exclude-pattern", "-p", help=HELP_EXCLUDE_PATTERNS)


def _include_patterns_option() -> Any:
    return typer.Option(None, "--include-pattern", "-i", help=HELP_INCLUDE_PATTERNS)


def _use_regex_option() -> Any:
    return typer.Option(False, "--regex", "-r", help=HELP_USE_REGEX)


def _ignore_file_option() -> Any:
    return typer.Option(None, "--ignore-file", "-g", help=HELP_IGNORE_FILE)


def _max_depth_option(help_text: str) -> Any:
    return typer.Option(0, "--depth", "-d", help=help_text)


def _show_full_path_option() -> Any:
    return typer.Option(False, "--full-path", "-l", help=HELP_SHOW_FULL_PATH)


def _sort_by_loc_option() -> Any:
    return typer.Option(False, "--sort-by-loc", "-s", help=HELP_SORT_BY_LOC)


def _sort_by_size_option() -> Any:
    return typer.Option(False, "--sort-by-size", "-z", help=HELP_SORT_BY_SIZE)


def _sort_by_mtime_option() -> Any:
    return typer.Option(False, "--sort-by-mtime", "-m", help=HELP_SORT_BY_MTIME)


def _sort_by_similarity_option() -> Any:
    return typer.Option(
        False, "--sort-by-similarity", "-S", help=HELP_SORT_BY_SIMILARITY
    )


def _show_git_status_option() -> Any:
    return typer.Option(
        False,
        "--git-status",
        "-G",
        help="Annotate files with Git status markers: [U] untracked, [M] modified, [A] added, [D] deleted",
    )


def _output_dir_option() -> Any:
    return typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for exports (defaults to current directory)",
    )


def _output_prefix_option(default: str) -> Any:
    return typer.Option(default, "--prefix", "-n", help="Prefix for exported filenames")


def _icon_style_option(help_text: str) -> Any:
    return typer.Option(None, "--icon-style", help=help_text)


def _verbose_option() -> Any:
    return typer.Option(False, "--verbose", "-v", help=HELP_VERBOSE)


config_app = typer.Typer(help="Manage recursivist user configuration")
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key (e.g., icon-style)"),
    value: str = typer.Argument(..., help="Configuration value (e.g., nerd or emoji)"),
) -> None:
    """Set a persistent configuration value.

    Writes a user preference to the global configuration file.
    Currently supports setting the `icon-style` to either `emoji` or `nerd`.

    Args:
        key: The configuration key to set (e.g., "icon-style").
        value: The value to assign to the key.

    Raises:
        typer.Exit: With exit code ``1`` if an invalid key or value
            is provided.

    Examples:
        >>> recursivist config set icon-style nerd
        >>> recursivist config set icon-style emoji
    """
    config_key = key.replace("-", "_")

    if config_key == "icon_style" and value not in ["emoji", "nerd"]:
        logger.error("Invalid value for icon-style. Use 'emoji' or 'nerd'.")
        raise typer.Exit(1)

    config = load_config()
    config[config_key] = value
    save_config(config)
    typer.echo(f"Configuration updated: {key} = '{value}'")


@app.callback()
def callback() -> None:
    """Recursivist CLI tool for directory visualization and export.

    Entry-point callback invoked by Typer before any subcommand is
    dispatched. It sets up the application context and makes top-level
    help text available.

    Available commands:
        visualize: Display a directory structure in the terminal.
        export: Export a directory structure to various file formats.
        compare: Compare two directory structures side by side.
        config: Manage user preferences.
        version: Display the current version.
        completion: Generate a shell completion script.
    """
    pass


def parse_list_option(option_value: list[str] | None) -> list[str]:
    """Parse a list option that may contain space-separated values.

    Handles two common CLI input styles for multi-value options:

    * Multiple flag repetitions: ``--exclude dir1 --exclude dir2``
    * Space-separated tokens in a single flag: ``--exclude "dir1 dir2"``

    Each raw value is split on whitespace and empty tokens are dropped,
    so callers always receive a clean flat list.

    Args:
        option_value: Raw list of strings collected by Typer for a
            repeatable option. Each element may itself contain
            multiple space-separated tokens. Pass ``None`` when the
            option was not provided.

    Returns:
        Flat list of non-empty, whitespace-stripped strings. Returns
        an empty list when *option_value* is ``None`` or contains no
        non-whitespace tokens.

    Examples:
        >>> parse_list_option(["node_modules .git", "__pycache__"])
        ['node_modules', '.git', '__pycache__']
        >>> parse_list_option(None)
        []
    """
    if not option_value:
        return []
    result = []
    for item in option_value:
        result.extend([x.strip() for x in item.split() if x.strip()])
    return result


def _log_display_options(
    max_depth: int,
    show_full_path: bool,
    sort_by_loc: bool,
    sort_by_size: bool,
    sort_by_mtime: bool,
    sort_by_similarity: bool = False,
) -> None:
    """Log the depth and display/sort options selected for a command.

    Emits the informational messages shared by the visualize, export,
    and compare commands when the corresponding option is active. Has
    no effect for options left at their defaults.

    Args:
        max_depth: Maximum directory depth; a message is logged when
            greater than ``0``.
        show_full_path: Whether full paths are shown.
        sort_by_loc: Whether files are sorted by lines of code.
        sort_by_size: Whether files are sorted by size.
        sort_by_mtime: Whether files are sorted by modification time.
        sort_by_similarity: Whether files are grouped by name similarity.
    """
    if max_depth > 0:
        logger.info(f"Limiting depth to {max_depth} levels")
    if show_full_path:
        logger.info(MSG_FULL_PATH)
    if sort_by_loc:
        logger.info(MSG_SORT_LOC)
    if sort_by_size:
        logger.info(MSG_SORT_SIZE)
    if sort_by_mtime:
        logger.info(MSG_SORT_MTIME)
    if sort_by_similarity:
        logger.info(MSG_SORT_SIMILARITY)


def _parse_filter_options(
    exclude_dirs: list[str] | None,
    exclude_extensions: list[str] | None,
    exclude_patterns: list[str] | None,
    include_patterns: list[str] | None,
    use_regex: bool,
) -> tuple[list[str], set[str], list[str], list[str]]:
    """Parse and normalize the shared exclude/include filter options.

    Splits space-separated values, normalizes excluded extensions to a
    lowercase, dot-prefixed set, and emits the same debug logging used
    by every command. This is the common preprocessing step shared by
    the visualize, export, and compare commands.

    Args:
        exclude_dirs: Raw directory-exclusion values from Typer.
        exclude_extensions: Raw extension-exclusion values from Typer.
        exclude_patterns: Raw exclude-pattern values from Typer.
        include_patterns: Raw include-pattern values from Typer.
        use_regex: Whether patterns are regex (affects log wording).

    Returns:
        A tuple of ``(parsed_exclude_dirs, exclude_exts_set,
        parsed_exclude_patterns, parsed_include_patterns)``.
    """
    parsed_exclude_dirs = parse_list_option(exclude_dirs)
    parsed_exclude_exts = parse_list_option(exclude_extensions)
    parsed_exclude_patterns = parse_list_option(exclude_patterns)
    parsed_include_patterns = parse_list_option(include_patterns)
    exclude_exts_set: set[str] = set()
    if parsed_exclude_exts:
        exclude_exts_set = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in parsed_exclude_exts
        }
        logger.debug(f"Excluding extensions: {exclude_exts_set}")
    if parsed_exclude_dirs:
        logger.debug(f"Excluding directories: {parsed_exclude_dirs}")
    if parsed_exclude_patterns:
        pattern_type = "regex" if use_regex else "glob"
        logger.debug(f"Excluding {pattern_type} patterns: {parsed_exclude_patterns}")
    if parsed_include_patterns:
        pattern_type = "regex" if use_regex else "glob"
        logger.debug(f"Including {pattern_type} patterns: {parsed_include_patterns}")
    return (
        parsed_exclude_dirs,
        exclude_exts_set,
        parsed_exclude_patterns,
        parsed_include_patterns,
    )


def _enable_verbose_if_requested(verbose: bool) -> None:
    """Lower the logger to DEBUG when verbose output is requested.

    Shared by the visualize, export, and compare commands so the
    verbose preamble is defined in exactly one place.

    Args:
        verbose: When ``True``, set the logger level to DEBUG and emit
            the standard "verbose mode enabled" debug message. When
            ``False``, do nothing.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug(MSG_VERBOSE)


def _resolve_and_validate_directory(directory: Path) -> Path:
    """Resolve a directory path and verify it points at a directory.

    Centralizes the existence/`is_dir` check shared by the visualize
    and export commands so the validation behavior and error message
    stay consistent.

    Args:
        directory: Raw directory path as received from Typer.

    Returns:
        The resolved (absolute) directory path.

    Raises:
        typer.Exit: With exit code ``1`` if the resolved path does not
            exist or is not a directory.
    """
    directory = directory.resolve()
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Error: {directory} is not a valid directory")
        raise typer.Exit(1)
    return directory


def _resolve_ignore_file(
    directories: list[Path], ignore_file: str | None
) -> str | None:
    """Resolve the ignore file name, optionally adding a leading dot.

    Checks if the provided ignore_file exists in any of the target directories.
    If it doesn't, but a version with a leading dot does, returns the dotted version.
    Otherwise, returns the original filename so normal warning logic proceeds.

    Args:
        directories: List of resolved directory paths to check for the ignore file.
        ignore_file: Filename of the ignore file to look for, or
            ``None`` when the option was not supplied.

    Returns:
        The resolved filename string (potentially with an added dot), or the
        original filename if no dotted version is found. Returns ``None`` if
        *ignore_file* is ``None``.
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


def _warn_if_ignore_file_missing(directory: Path, ignore_file: str | None) -> None:
    """Log whether the requested ignore file exists inside *directory*.

    Emits a debug message when the ignore file is found and a warning
    when it is requested but absent. Does nothing when no ignore file
    was requested. Shared by the visualize and export commands.

    Args:
        directory: Directory in which to look for the ignore file.
        ignore_file: Filename of the ignore file to look for, or
            ``None`` when the option was not supplied.
    """
    if not ignore_file:
        return
    ignore_path = directory / ignore_file
    if ignore_path.exists():
        logger.debug(f"Using ignore file: {ignore_path}")
    else:
        logger.warning(f"Ignore file not found: {ignore_path}")


def _compile_patterns_for_scan(
    parsed_exclude_patterns: list[str],
    parsed_include_patterns: list[str],
    use_regex: bool,
) -> tuple[list[str | Pattern[str]], list[str | Pattern[str]]]:
    """Compile exclude/include patterns for the scanner.

    When *use_regex* is ``True`` the patterns are compiled to regular
    expressions; otherwise the plain glob strings are passed through
    unchanged (cast to the scanner's expected type). Shared by the
    visualize and export commands.

    Args:
        parsed_exclude_patterns: Flat list of exclude-pattern strings.
        parsed_include_patterns: Flat list of include-pattern strings.
        use_regex: Whether the patterns should be treated as regex.

    Returns:
        A ``(compiled_exclude, compiled_include)`` tuple suitable for
        passing directly to :func:`get_directory_structure`.
    """
    if use_regex:
        compiled_exclude = compile_regex_patterns(parsed_exclude_patterns, use_regex)
        compiled_include = compile_regex_patterns(parsed_include_patterns, use_regex)
    else:
        compiled_exclude = cast(list[str | Pattern[str]], parsed_exclude_patterns)
        compiled_include = cast(list[str | Pattern[str]], parsed_include_patterns)
    return compiled_exclude, compiled_include


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
    sort_by_loc: bool,
    sort_by_size: bool,
    sort_by_mtime: bool,
    show_git_status: bool,
) -> tuple[dict[str, Any], set[str]]:
    """Fetch Git status and scan *directory* into a tree structure.

    Encapsulates the scanning pipeline shared by the visualize and
    export commands: optionally resolving the Git status map, compiling
    patterns, running the scan under a progress indicator, and logging
    the number of unique extensions found.

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
        sort_by_loc: Whether to compute lines-of-code counts.
        sort_by_size: Whether to compute file sizes.
        sort_by_mtime: Whether to compute modification times.
        show_git_status: Whether to annotate files with Git status.

    Returns:
        A ``(structure, extensions)`` tuple as produced by
        :func:`get_directory_structure`.
    """
    git_status_map: dict[str, str] | None = None
    if show_git_status:
        git_status_map = get_git_status(str(directory))
        if not git_status_map:
            logger.debug(
                "Git status requested but no data returned — "
                "directory may not be inside a Git repository, or there are no changes."
            )
    with Progress() as progress:
        task_scan = progress.add_task(
            "[cyan]Scanning directory structure...", total=None
        )
        compiled_exclude, compiled_include = _compile_patterns_for_scan(
            parsed_exclude_patterns,
            parsed_include_patterns,
            use_regex,
        )
        structure, extensions = get_directory_structure(
            str(directory),
            parsed_exclude_dirs,
            ignore_file,
            exclude_exts_set,
            exclude_patterns=compiled_exclude,
            include_patterns=compiled_include,
            max_depth=max_depth,
            show_full_path=show_full_path,
            sort_by_loc=sort_by_loc,
            sort_by_size=sort_by_size,
            sort_by_mtime=sort_by_mtime,
            show_git_status=show_git_status,
            git_status_map=git_status_map,
        )
        progress.update(task_scan, completed=True)
        logger.debug(f"Found {len(extensions)} unique file extensions")
    return structure, extensions


@app.command()
def visualize(
    directory: Path = typer.Argument(
        ".", help="Directory path to visualize (defaults to current directory)"
    ),
    exclude_dirs: list[str] | None = _exclude_dirs_option(),
    exclude_extensions: list[str] | None = _exclude_extensions_option(),
    exclude_patterns: list[str] | None = _exclude_patterns_option(),
    include_patterns: list[str] | None = _include_patterns_option(),
    use_regex: bool = _use_regex_option(),
    ignore_file: str | None = _ignore_file_option(),
    max_depth: int = _max_depth_option("Maximum depth to display (0 for unlimited)"),
    show_full_path: bool = _show_full_path_option(),
    sort_by_loc: bool = _sort_by_loc_option(),
    sort_by_size: bool = _sort_by_size_option(),
    sort_by_mtime: bool = _sort_by_mtime_option(),
    sort_by_similarity: bool = _sort_by_similarity_option(),
    show_git_status: bool = _show_git_status_option(),
    icon_style: str | None = _icon_style_option(
        "Override icon style ('emoji' or 'nerd'). Defaults to user config."
    ),
    verbose: bool = _verbose_option(),
) -> None:
    """Visualize a directory structure as a tree in the terminal.

    Scans *directory* and renders a rich, color-coded tree to stdout.
    File-extension colors, optional statistics, and Git status markers
    can be enabled through the available options. An animated progress
    indicator is shown while scanning large directories.

    Args:
        directory: Root directory to visualize. Must exist and be a
            directory. Defaults to the current working directory.
        exclude_dirs: Directory names to omit from the tree entirely
            (e.g. ``["node_modules", ".git"]``).
        exclude_extensions: File extensions to hide. Values are
            normalized so both ``"pyc"`` and ``".pyc"`` are accepted.
        exclude_patterns: Glob or regex patterns for file/directory
            names to exclude. Interpretation depends on *use_regex*.
        include_patterns: Patterns that *override* exclusions — any
            path matching an include pattern is shown even if it
            would otherwise be filtered out.
        use_regex: When ``True``, treat *exclude_patterns* and
            *include_patterns* as Python regular expressions instead
            of glob patterns.
        ignore_file: Filename of an ignore file located inside
            *directory* (e.g. ``".gitignore"``). Entries in that file
            are treated as additional exclusions.
        max_depth: Maximum directory depth to display. ``0`` means
            unlimited.
        show_full_path: When ``True``, display absolute paths instead
            of bare filenames.
        sort_by_loc: When ``True``, sort files by lines-of-code count
            (descending) and annotate each file with its LOC count.
        sort_by_size: When ``True``, sort files by size (descending)
            and annotate each file with its size.
        sort_by_mtime: When ``True``, sort files by last-modification
            time (newest first) and annotate each file with its
            timestamp.
        sort_by_similarity: When ``True``, group files with similar
            names next to each other. Has no effect when a numeric
            sort (LOC, size, or mtime) is also active.
        show_git_status: When ``True``, annotate files with their Git status:
            ``[U]`` untracked, ``[M]`` modified, ``[A]`` added, ``[D]``
            deleted.
        icon_style: Icon style to use for file/folder markers. If not
            provided, falls back to the persistent user config.
        verbose: When ``True``, lower the log level to DEBUG so that
            internal processing steps are printed to the terminal.

    Raises:
        typer.Exit: With exit code ``1`` if *directory* does not exist
            or is not a directory, or if any unhandled exception occurs
            during scanning or rendering.

    Examples:
        >>> # Display current directory
        >>> recursivist visualize
        >>> # Display a specific directory
        >>> recursivist visualize /path/to/project
        >>> # Exclude directories
        >>> recursivist visualize -e node_modules .git
        >>> # Exclude file extensions
        >>> recursivist visualize -x .pyc .log
        >>> # Exclude glob patterns
        >>> recursivist visualize -p "*.test.js" "*.spec.js"
        >>> # Exclude regex patterns
        >>> recursivist visualize -p ".*test.*" -r
        >>> # Include overrides
        >>> recursivist visualize -i "src/*" "*.md"
        >>> # Limit depth to 2
        >>> recursivist visualize -d 2
        >>> # Override icon style for this run
        >>> recursivist visualize --icon-style nerd
    """
    _enable_verbose_if_requested(verbose)

    resolved_style = icon_style or USER_CONFIG.get("icon_style", "emoji")
    directory = _resolve_and_validate_directory(directory)
    ignore_file = _resolve_ignore_file([directory], ignore_file)

    _log_display_options(
        max_depth,
        show_full_path,
        sort_by_loc,
        sort_by_size,
        sort_by_mtime,
        sort_by_similarity,
    )
    if show_git_status:
        logger.info("Annotating files with Git status markers")
    (
        parsed_exclude_dirs,
        exclude_exts_set,
        parsed_exclude_patterns,
        parsed_include_patterns,
    ) = _parse_filter_options(
        exclude_dirs,
        exclude_extensions,
        exclude_patterns,
        include_patterns,
        use_regex,
    )
    _warn_if_ignore_file_missing(directory, ignore_file)
    try:
        structure, extensions = _scan_directory(
            directory,
            parsed_exclude_dirs,
            ignore_file,
            exclude_exts_set,
            parsed_exclude_patterns,
            parsed_include_patterns,
            use_regex,
            max_depth,
            show_full_path,
            sort_by_loc,
            sort_by_size,
            sort_by_mtime,
            show_git_status,
        )
        logger.info("Displaying directory tree:")
        display_tree(
            str(directory),
            parsed_exclude_dirs,
            ignore_file,
            exclude_exts_set,
            parsed_exclude_patterns,
            parsed_include_patterns,
            use_regex,
            max_depth,
            show_full_path,
            sort_by_loc,
            sort_by_size,
            sort_by_mtime,
            show_git_status,
            icon_style=resolved_style,
            structure=structure,
            extensions=extensions,
            sort_by_similarity=sort_by_similarity,
        )
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        raise typer.Exit(1) from None


@app.command()
def export(
    directory: Path = typer.Argument(
        ".", help="Directory path to export (defaults to current directory)"
    ),
    formats: list[str] = typer.Option(
        ["md"],
        "--format",
        "-f",
        help="Export formats: txt, json, html, md, jsx, svg, rst",
    ),
    output_dir: Path | None = _output_dir_option(),
    output_prefix: str | None = _output_prefix_option("structure"),
    exclude_dirs: list[str] | None = _exclude_dirs_option(),
    exclude_extensions: list[str] | None = _exclude_extensions_option(),
    exclude_patterns: list[str] | None = _exclude_patterns_option(),
    include_patterns: list[str] | None = _include_patterns_option(),
    use_regex: bool = _use_regex_option(),
    ignore_file: str | None = _ignore_file_option(),
    max_depth: int = _max_depth_option("Maximum depth to export (0 for unlimited)"),
    show_full_path: bool = _show_full_path_option(),
    sort_by_loc: bool = _sort_by_loc_option(),
    sort_by_size: bool = _sort_by_size_option(),
    sort_by_mtime: bool = _sort_by_mtime_option(),
    sort_by_similarity: bool = _sort_by_similarity_option(),
    show_git_status: bool = _show_git_status_option(),
    icon_style: str | None = _icon_style_option(
        "Override icon style. Defaults to 'emoji' for safe file exports."
    ),
    verbose: bool = _verbose_option(),
) -> None:
    """Export a directory structure to one or more file formats.

    Scans *directory*, builds the internal tree representation, and
    writes output files without rendering anything to the terminal.
    Multiple formats can be requested in a single invocation; each
    format produces a separate file named ``<prefix>.<format>`` inside
    *output_dir*. By default, this forces the `emoji` icon style to
    ensure cross-platform compatibility in external viewers, unless
    explicitly overridden.

    Args:
        directory: Root directory to export. Must exist and be a
            directory. Defaults to the current working directory.
        formats: Export format identifiers. Supported values are
            ``"txt"``, ``"json"``, ``"html"``, ``"md"``, ``"jsx"``,
            ``"svg"``, and ``"rst"``. Multiple formats may be given as
            separate flags or as a single space-separated string.
        output_dir: Directory where exported files are written.
            Created automatically if it does not exist. Defaults to
            the current working directory.
        output_prefix: Filename prefix shared by all exported files.
            Defaults to ``"structure"``.
        exclude_dirs: Directory names to omit from the exported tree.
        exclude_extensions: File extensions to hide. Values are
            normalized so both ``"pyc"`` and ``".pyc"`` are accepted.
        exclude_patterns: Glob or regex patterns for file/directory
            names to exclude. Interpretation depends on *use_regex*.
        include_patterns: Patterns that override exclusions — any
            path matching an include pattern is exported even if it
            would otherwise be filtered out.
        use_regex: When ``True``, treat *exclude_patterns* and
            *include_patterns* as Python regular expressions instead
            of glob patterns.
        ignore_file: Filename of an ignore file inside *directory*
            (e.g. ``".gitignore"``). Entries are treated as additional
            exclusions.
        max_depth: Maximum directory depth to include in the export.
            ``0`` means unlimited.
        show_full_path: When ``True``, write absolute paths instead of
            bare filenames.
        sort_by_loc: When ``True``, sort files by lines-of-code count
            (descending) and annotate each file with its LOC count.
        sort_by_size: When ``True``, sort files by size (descending)
            and annotate each file with its size.
        sort_by_mtime: When ``True``, sort files by last-modification
            time (newest first) and annotate each file with its
            timestamp.
        sort_by_similarity: When ``True``, group files with similar
            names next to each other. Has no effect when a numeric
            sort (LOC, size, or mtime) is also active.
        show_git_status: When ``True``, annotate files with their Git
            status markers in the exported output.
        icon_style: Icon style to enforce on the export. Defaults to
            'emoji' for external compatibility unless provided.
        verbose: When ``True``, lower the log level to DEBUG so that
            internal processing steps are printed to the terminal.

    Raises:
        typer.Exit: With exit code ``1`` if *directory* is invalid,
            an unsupported format is requested, or an unhandled
            exception occurs during scanning or file writing.

    Examples:
        >>> # Export current directory to Markdown
        >>> recursivist export
        >>> # Export a specific directory
        >>> recursivist export /path/to/project
        >>> # Multiple formats (space-separated)
        >>> recursivist export -f "json md html"
        >>> # Force export with nerd fonts
        >>> recursivist export --icon-style nerd
    """
    _enable_verbose_if_requested(verbose)

    resolved_style = icon_style or "emoji"
    directory = _resolve_and_validate_directory(directory)
    ignore_file = _resolve_ignore_file([directory], ignore_file)

    _log_display_options(
        max_depth,
        show_full_path,
        sort_by_loc,
        sort_by_size,
        sort_by_mtime,
        sort_by_similarity,
    )
    if show_git_status:
        logger.info("Annotating files with Git status markers")
    (
        parsed_exclude_dirs,
        exclude_exts_set,
        parsed_exclude_patterns,
        parsed_include_patterns,
    ) = _parse_filter_options(
        exclude_dirs,
        exclude_extensions,
        exclude_patterns,
        include_patterns,
        use_regex,
    )
    _warn_if_ignore_file_missing(directory, ignore_file)
    try:
        structure, extensions = _scan_directory(
            directory,
            parsed_exclude_dirs,
            ignore_file,
            exclude_exts_set,
            parsed_exclude_patterns,
            parsed_include_patterns,
            use_regex,
            max_depth,
            show_full_path,
            sort_by_loc,
            sort_by_size,
            sort_by_mtime,
            show_git_status,
        )
        parsed_formats = []
        for fmt in formats:
            parsed_formats.extend([x.strip() for x in fmt.split(" ") if x.strip()])
        valid_formats = ["txt", "json", "html", "md", "jsx", "svg", "rst"]
        invalid_formats = [
            fmt for fmt in parsed_formats if fmt.lower() not in valid_formats
        ]
        if invalid_formats:
            logger.error(f"Unsupported export format(s): {', '.join(invalid_formats)}")
            logger.info(f"Supported formats: {', '.join(valid_formats)}")
            raise typer.Exit(1)
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(".")
        logger.info(f"Exporting to {len(parsed_formats)} format(s)")
        for fmt in parsed_formats:
            output_path = output_dir / f"{output_prefix}.{fmt.lower()}"
            try:
                exporter = get_exporter(
                    format_type=fmt.lower(),
                    structure=structure,
                    root_name=os.path.basename(str(directory)),
                    base_path=str(directory) if show_full_path else None,
                    sort_by_loc=sort_by_loc,
                    sort_by_size=sort_by_size,
                    sort_by_mtime=sort_by_mtime,
                    show_git_status=show_git_status,
                    icon_style=resolved_style,
                    sort_by_similarity=sort_by_similarity,
                )
                exporter.export(str(output_path))
                logger.info(f"Successfully exported to {output_path}")
            except Exception as e:
                logger.exception(f"Failed to export to {fmt}: {e}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        raise typer.Exit(1) from None


@app.command()
def completion(
    shell: str = typer.Argument(..., help="Shell type (bash, zsh, fish, powershell)"),
) -> None:
    """Generate a shell completion script for the recursivist CLI.

    Writes a shell-specific snippet to stdout that can be sourced (or
    piped into the shell's eval mechanism) to enable tab-completion for
    all recursivist commands, options, and arguments.

    Args:
        shell: Target shell for the completion script. Must be one of
            ``"bash"``, ``"zsh"``, ``"fish"``, or ``"powershell"``
            (case-insensitive).

    Raises:
        typer.Exit: With exit code ``1`` if *shell* is not a supported
            value or if an error occurs while generating the script.

    Examples:
        >>> recursivist completion bash        # Bash
        >>> recursivist completion zsh         # Zsh
        >>> recursivist completion fish        # Fish
        >>> recursivist completion powershell  # PowerShell
    """
    try:
        valid_shells = ["bash", "zsh", "fish", "powershell"]
        if shell.lower() not in valid_shells:
            logger.error(f"Unsupported shell: {shell}")
            logger.info(f"Supported shells: {', '.join(valid_shells)}")
            raise typer.Exit(1)
        completion_script = ""
        if shell.lower() == "bash":
            completion_script = f'eval "$({sys.argv[0]} --completion-script bash)"'
        elif shell.lower() == "zsh":
            completion_script = f'eval "$({sys.argv[0]} --completion-script zsh)"'
        elif shell.lower() == "fish":
            completion_script = f"{sys.argv[0]} --completion-script fish | source"
        elif shell.lower() == "powershell":
            completion_script = f"& {sys.argv[0]} --completion-script powershell | Out-String | Invoke-Expression"
        typer.echo(completion_script)
        logger.info(f"Generated completion script for {shell}")
    except Exception as e:
        logger.exception(f"Error generating completion script: {e}")
        raise typer.Exit(1) from None


@app.command()
def version() -> None:
    """Display the current version of recursivist.

    Reads the version string from the installed package metadata and
    prints it to stdout in the format
    ``"Recursivist version: <version>"``.
    """
    from recursivist import __version__

    typer.echo(f"Recursivist version: {__version__}")


@app.command()
def compare(
    dir1: Path = typer.Argument(
        ...,
        help="First directory path to compare",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    dir2: Path = typer.Argument(
        ...,
        help="Second directory path to compare",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    exclude_dirs: list[str] | None = _exclude_dirs_option(),
    exclude_extensions: list[str] | None = _exclude_extensions_option(),
    exclude_patterns: list[str] | None = _exclude_patterns_option(),
    include_patterns: list[str] | None = _include_patterns_option(),
    use_regex: bool = _use_regex_option(),
    ignore_file: str | None = _ignore_file_option(),
    max_depth: int = _max_depth_option("Maximum depth to display (0 for unlimited)"),
    save_as_html: bool = typer.Option(
        False,
        "--save",
        "-f",
        help="Save comparison as HTML file instead of displaying in terminal",
    ),
    output_dir: Path | None = _output_dir_option(),
    output_prefix: str | None = _output_prefix_option("comparison"),
    show_full_path: bool = _show_full_path_option(),
    sort_by_loc: bool = _sort_by_loc_option(),
    sort_by_size: bool = _sort_by_size_option(),
    sort_by_mtime: bool = _sort_by_mtime_option(),
    sort_by_similarity: bool = _sort_by_similarity_option(),
    icon_style: str | None = _icon_style_option(
        "Override icon style. Defaults to 'emoji' if saving to HTML, else user config."
    ),
    verbose: bool = _verbose_option(),
) -> None:
    """Compare two directory structures side by side.

    Builds the tree for each directory using identical filtering
    options, then renders a color-highlighted side-by-side diff.
    Items present only in *dir1* are highlighted in one color; items
    present only in *dir2* in another; shared items are shown normally.
    A legend is included in the output. When *save_as_html* is
    ``True`` the comparison is written to an HTML file instead.

    By default, uses the persistent user configuration for icon styling
    in the terminal. If exported to HTML, strictly falls back to
    the 'emoji' style to ensure cross-platform compatibility.

    Args:
        dir1: First directory to compare. Must exist and be a
            directory (validated by Typer before the function runs).
        dir2: Second directory to compare. Must exist and be a
            directory (validated by Typer before the function runs).
        exclude_dirs: Directory names to omit from both trees.
        exclude_extensions: File extensions to hide from both trees.
            Values are normalized so both ``"pyc"`` and ``".pyc"``
            are accepted.
        exclude_patterns: Glob or regex patterns for file/directory
            names to exclude from both trees. Interpretation depends
            on *use_regex*.
        include_patterns: Patterns that override exclusions — any
            path matching an include pattern is shown even if it
            would otherwise be filtered out.
        use_regex: When ``True``, treat *exclude_patterns* and
            *include_patterns* as Python regular expressions instead
            of glob patterns.
        ignore_file: Filename of an ignore file to look for inside
            each directory (e.g. ``".gitignore"``).
        max_depth: Maximum directory depth to display. ``0`` means
            unlimited.
        save_as_html: When ``True``, write the comparison to an HTML
            file rather than printing to the terminal.
        output_dir: Directory where the HTML file is written when
            *save_as_html* is ``True``. Created if it does not exist.
            Defaults to the current working directory.
        output_prefix: Filename prefix for the exported HTML file.
            Defaults to ``"comparison"``.
        show_full_path: When ``True``, display absolute paths instead
            of bare filenames.
        sort_by_loc: When ``True``, sort files by lines-of-code count
            (descending) and annotate each file with its LOC count.
        sort_by_size: When ``True``, sort files by size (descending)
            and annotate each file with its size.
        sort_by_mtime: When ``True``, sort files by last-modification
            time (newest first) and annotate each file with its
            timestamp.
        sort_by_similarity: When ``True``, group files with similar
            names next to each other. Has no effect when a numeric
            sort (LOC, size, or mtime) is also active.
        icon_style: Style to use for folder and file icons. Will use
            the user configuration when visualizing in terminal, and
            default to 'emoji' when outputting to HTML.
        verbose: When ``True``, lower the log level to DEBUG so that
            internal processing steps are printed to the terminal.

    Raises:
        typer.Exit: With exit code ``1`` if an unhandled exception
            occurs during comparison or export.

    Examples:
        >>> # Basic comparison
        >>> recursivist compare dir1 dir2
        >>> # Exclude a directory
        >>> recursivist compare dir1 dir2 -e node_modules
        >>> # Exclude extensions
        >>> recursivist compare dir1 dir2 -x .pyc .log
        >>> # Exclude glob patterns
        >>> recursivist compare dir1 dir2 -p "*.test.js"
        >>> # Exclude regex patterns
        >>> recursivist compare dir1 dir2 -p ".*test.*" -r
        >>> # Include overrides
        >>> recursivist compare dir1 dir2 -i "src/*"
        >>> # Limit depth to 2
        >>> recursivist compare dir1 dir2 -d 2
        >>> # Show full paths
        >>> recursivist compare dir1 dir2 -l
        >>> # Export to HTML
        >>> recursivist compare dir1 dir2 -f
        >>> # Override icon styling
        >>> recursivist compare dir1 dir2 --icon-style nerd
    """
    _enable_verbose_if_requested(verbose)
    logger.info(f"Comparing directories: {dir1} and {dir2}")

    ignore_file = _resolve_ignore_file([dir1, dir2], ignore_file)

    _log_display_options(
        max_depth,
        show_full_path,
        sort_by_loc,
        sort_by_size,
        sort_by_mtime,
        sort_by_similarity,
    )

    if icon_style:
        resolved_style = icon_style
    elif save_as_html:
        resolved_style = "emoji"
    else:
        resolved_style = USER_CONFIG.get("icon_style", "emoji")

    (
        parsed_exclude_dirs,
        exclude_exts_set,
        parsed_exclude_patterns,
        parsed_include_patterns,
    ) = _parse_filter_options(
        exclude_dirs,
        exclude_extensions,
        exclude_patterns,
        include_patterns,
        use_regex,
    )
    if ignore_file:
        for d in [dir1, dir2]:
            ignore_path = d / ignore_file
            if ignore_path.exists():
                logger.debug(f"Using ignore file from {d}: {ignore_path}")
            else:
                logger.warning(f"Ignore file not found in {d}: {ignore_path}")
    try:
        actual_ignore_file = "" if ignore_file is None else ignore_file
        if save_as_html:
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(".")
            output_path = output_dir / f"{output_prefix}.html"
            try:
                export_comparison(
                    str(dir1),
                    str(dir2),
                    "html",
                    str(output_path),
                    parsed_exclude_dirs,
                    actual_ignore_file,
                    exclude_exts_set,
                    exclude_patterns=parsed_exclude_patterns,
                    include_patterns=parsed_include_patterns,
                    use_regex=use_regex,
                    max_depth=max_depth,
                    show_full_path=show_full_path,
                    sort_by_loc=sort_by_loc,
                    sort_by_size=sort_by_size,
                    sort_by_mtime=sort_by_mtime,
                    icon_style=resolved_style,
                    sort_by_similarity=sort_by_similarity,
                )
                logger.info(f"Successfully exported to {output_path}")
            except Exception as e:
                logger.exception(f"Failed to export to HTML: {e}")
        else:
            display_comparison(
                str(dir1),
                str(dir2),
                parsed_exclude_dirs,
                actual_ignore_file,
                exclude_exts_set,
                exclude_patterns=parsed_exclude_patterns,
                include_patterns=parsed_include_patterns,
                use_regex=use_regex,
                max_depth=max_depth,
                show_full_path=show_full_path,
                sort_by_loc=sort_by_loc,
                sort_by_size=sort_by_size,
                sort_by_mtime=sort_by_mtime,
                icon_style=resolved_style,
                sort_by_similarity=sort_by_similarity,
            )
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        raise typer.Exit(1) from None


def main() -> None:
    """Entry point for the recursivist CLI application.

    Invokes the Typer application, which parses command-line arguments
    and dispatches to the appropriate subcommand function. This
    function is registered as the ``recursivist`` console-script entry
    point in the package configuration.
    """
    app()


if __name__ == "__main__":
    main()
