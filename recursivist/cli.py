#!/usr/bin/env python3
"""Recursivist CLI - A beautiful directory structure visualization tool.

Provides the command-line interface for the recursivist package, letting
users visualize directory structures, export them in various formats,
compare two structures side-by-side, manage user configurations, and
generate shell completion scripts.

Main commands:
    visualize: Display a directory structure in the terminal with rich
        formatting and optional statistics.
    export: Export a directory structure to TXT, JSON, HTML, MD,
        SVG, or RST.
    compare: Compare two directory structures with highlighted
        differences.
    config: Manage persistent user preferences like icon styles.
    version: Display the current version information.
    completion: Generate shell completion scripts for various shells.

The visualize, export, and compare commands accept a GitHub repository URL
anywhere they accept a local directory; see :mod:`recursivist.github`.

All commands share a consistent set of filtering and display options:
    - Exclude directories, file extensions, glob, or regex patterns.
    - Include specific patterns that override exclusions.
    - Support for .gitignore and similar ignore files.
    - Depth limitation for large directories.
    - Full-path display option.
    - File statistics with sorting by lines of code, size, or
      modification time.
"""

import contextlib
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
from recursivist.flags import DisplayOptions, resolve_display_options
from recursivist.git_status import get_git_status
from recursivist.github import (
    GitHubError,
    GitHubTarget,
    apply_github_urls,
    checkout_repository,
    commit_shas_equal,
    get_github_token,
    parse_github_url,
    resolve_commit_shas,
)
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
HELP_SHOW_FULL_PATH = (
    "Show full paths instead of just filenames "
    "(GitHub blob URLs for GitHub repositories)"
)
HELP_SORT_BY_LOC = "Sort files by lines of code and display LOC counts"
HELP_SORT_BY_SIZE = "Sort files by size and display file sizes"
HELP_SORT_BY_MTIME = "Sort files by modification time and display timestamps"
HELP_SORT_BY_GIT_STATUS = "Sort files by Git status and display status markers"
HELP_SORT_BY_SIMILARITY = (
    "Group files with similar names together (overridden by other sort options)"
)
HELP_LOC = "Display lines of code without affecting sort order"
HELP_SIZE = "Display file sizes without affecting sort order"
HELP_MTIME = "Display modification times without affecting sort order"
HELP_GIT_STATUS = (
    "Display Git status markers without affecting sort order: "
    "[U] untracked, [M] modified, [A] added, [D] deleted"
)
HELP_VERBOSE = "Enable verbose output"

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


def _sort_by_git_status_option() -> Any:
    return typer.Option(False, "--sort-by-git-status", help=HELP_SORT_BY_GIT_STATUS)


def _loc_option() -> Any:
    return typer.Option(False, "--loc", help=HELP_LOC)


def _size_option() -> Any:
    return typer.Option(False, "--size", help=HELP_SIZE)


def _mtime_option() -> Any:
    return typer.Option(False, "--mtime", help=HELP_MTIME)


def _show_git_status_option() -> Any:
    return typer.Option(False, "--git-status", "-G", help=HELP_GIT_STATUS)


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
    spec: DisplayOptions,
) -> None:
    """Log the depth and resolved display/sort options for a command.

    Emits the informational messages shared by the visualize, export, and
    compare commands, driven by the already-resolved :class:`DisplayOptions`:
    the single active sort key (if any), each displayed metric in order, and
    whether Git-status markers are shown. Has no effect for options left at
    their defaults.

    Args:
        max_depth: Maximum directory depth; a message is logged when greater
            than ``0``.
        show_full_path: Whether full paths are shown.
        spec: The resolved sorting and annotation directives to report.
    """
    if max_depth > 0:
        level_word = "level" if max_depth == 1 else "levels"
        logger.info(f"Limiting depth to {max_depth} {level_word}")
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


def _log_ignored_remote_flags(
    ignore_file: str | None,
    sort_by_git_status: bool,
    show_git_status: bool,
    sort_by_mtime: bool,
    show_mtime: bool,
) -> None:
    """Report which options are being skipped for a GitHub input.

    The ``--ignore-file``, ``--git-status``, ``--sort-by-git-status``,
    ``--mtime`` and ``--sort-by-mtime`` options are not meaningful for a hosted
    repository (see :mod:`recursivist.github`); when any were supplied for a
    GitHub input, this logs an informational message naming them so the behavior
    is not silent.

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
            "Ignoring "
            + ", ".join(ignored)
            + " for GitHub repository (not applicable to hosted repositories)"
        )


def _same_github_target(
    target1: GitHubTarget,
    target2: GitHubTarget,
    token: str | None,
) -> bool:
    """Return whether two GitHub targets refer to the same scanned tree.

    Owner and repository names are compared case-insensitively because
    GitHub treats them that way, while the subpath is compared
    case-sensitively because file paths are case-sensitive.

    When both sides pin the same ref (or neither does, so both use the
    default branch), no network access is needed. Otherwise the two refs
    are resolved to the commits they point at and compared, so that
    distinct refs that name the same commit — a branch and a tag on the
    same tip, a branch and the default branch, or a branch and an explicit
    commit SHA — are recognized as the same. If either ref cannot be
    resolved (repository missing, private, unreachable, or the ref does not
    exist), the targets are treated as *not* the same so the normal
    comparison flow can surface the real error rather than a misleading
    "compare with itself" message.

    Args:
        target1: The first parsed GitHub target.
        target2: The second parsed GitHub target.
        token: Optional GitHub token used for the ref lookups.

    Returns:
        ``True`` if both targets resolve to the same repository, commit and
        subtree, else ``False``.
    """
    if (
        target1.owner.lower() != target2.owner.lower()
        or target1.repo.lower() != target2.repo.lower()
        or target1.subpath != target2.subpath
    ):
        return False
    if target1.ref == target2.ref:
        return True
    try:
        sha1, sha2 = resolve_commit_shas(target1, [target1.ref, target2.ref], token)
    except GitHubError:
        return False
    return commit_shas_equal(sha1, sha2)


def _compare_inputs_are_same(
    dir1: str,
    dir2: str,
    target1: GitHubTarget | None,
    target2: GitHubTarget | None,
) -> bool:
    """Return whether both ``compare`` inputs refer to the same target.

    Comparing a structure against itself produces a diff in which every
    item is shared and nothing is unique, which is never what the caller
    intends. This detects that case so the :func:`compare` command can
    reject it instead of doing pointless work.

    The two inputs are considered the same when:

    * both are GitHub repositories that resolve to the same repository,
      ref and subtree — see :func:`_same_github_target` for how owner/repo
      case-insensitivity and the default branch are handled; or
    * both are local directories whose resolved absolute paths are equal,
      so that ``dir`` and ``dir/``, relative and absolute spellings, and
      symlinks pointing at the same location are all recognized as
      identical.

    A local directory and a GitHub repository are never the same.

    Args:
        dir1: The first raw input as given on the command line.
        dir2: The second raw input as given on the command line.
        target1: The parsed GitHub target for *dir1*, or ``None`` if it is
            a local path.
        target2: The parsed GitHub target for *dir2*, or ``None`` if it is
            a local path.

    Returns:
        ``True`` if the two inputs refer to the same target, else ``False``.
    """
    if target1 is not None and target2 is not None:
        return _same_github_target(target1, target2, get_github_token())
    if target1 is None and target2 is None:
        try:
            return Path(dir1).resolve() == Path(dir2).resolve()
        except OSError:
            return Path(dir1).absolute() == Path(dir2).absolute()
    return False


@app.command()
def visualize(
    directory: str = typer.Argument(
        ".",
        help=(
            "Directory path or GitHub repository URL to visualize "
            "(defaults to current directory)"
        ),
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
    sort_by_git_status: bool = _sort_by_git_status_option(),
    sort_by_similarity: bool = _sort_by_similarity_option(),
    loc: bool = _loc_option(),
    size: bool = _size_option(),
    mtime: bool = _mtime_option(),
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

    *directory* may also be a GitHub repository URL (optionally pinning a
    branch/tag and subtree via ``/tree/<ref>`` or ``/tree/<ref>/<subpath>``),
    in which case the
    repository is downloaded and scanned like a local directory. For a GitHub
    input the ``--ignore-file``, ``--git-status``, ``--sort-by-git-status``,
    ``--mtime`` and ``--sort-by-mtime`` options do not apply and are skipped,
    while ``--full-path`` shows each file's GitHub blob URL instead of a
    filesystem path.

    Sorting and annotation flags are resolved strictly by their left-to-right
    order on the command line: only the first sorting flag (``--sort-by-*``)
    takes effect, while every display-only flag (``--loc``, ``--size``,
    ``--mtime``, ``--git-status``) always annotates, in the order given. See
    :mod:`recursivist.flags` for the full resolution rules.

    Args:
        directory: Root directory to visualize, or a GitHub repository URL.
            Must exist and be a directory when local. Defaults to the current
            working directory.
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
            Ignored entirely if an earlier sorting flag was given.
        sort_by_size: When ``True``, sort files by size (descending)
            and annotate each file with its size. Ignored entirely if
            an earlier sorting flag was given.
        sort_by_mtime: When ``True``, sort files by last-modification
            time (newest first) and annotate each file with its
            timestamp. Ignored entirely if an earlier sorting flag was
            given.
        sort_by_git_status: When ``True``, sort files by Git status and
            annotate each file with its status marker. Ignored entirely
            if an earlier sorting flag was given.
        sort_by_similarity: When ``True``, group files with similar
            names next to each other. Ignored entirely if an earlier
            sorting flag was given.
        loc: When ``True``, display each file's lines-of-code count
            without affecting the sort order.
        size: When ``True``, display each file's size without affecting
            the sort order.
        mtime: When ``True``, display each file's modification time
            without affecting the sort order.
        show_git_status: When ``True``, annotate files with their Git status
            without affecting the sort order: ``[U]`` untracked, ``[M]``
            modified, ``[A]`` added, ``[D]`` deleted.
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
        >>> # Visualize a GitHub repository
        >>> recursivist visualize https://github.com/ArmaanjeetSandhu/recursivist
        >>> # Visualize a subtree on a specific branch, showing blob URLs
        >>> recursivist visualize https://github.com/owner/repo/tree/main/src -l
    """
    _enable_verbose_if_requested(verbose)

    resolved_style = icon_style or USER_CONFIG.get("icon_style", "emoji")
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
    )

    validated: Path = Path(directory)
    if is_remote:
        _log_ignored_remote_flags(
            ignore_file, sort_by_git_status, show_git_status, sort_by_mtime, mtime
        )
        ignore_file = None
    else:
        validated = _resolve_and_validate_directory(Path(directory))
        ignore_file = _resolve_ignore_file([validated], ignore_file)

    _log_display_options(max_depth, show_full_path, spec)
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
    try:
        with contextlib.ExitStack() as stack:
            if target is not None:
                checkout = stack.enter_context(checkout_repository(target))
                scan_dir = checkout.local_root
                root_name = checkout.root_name
            else:
                checkout = None
                scan_dir = str(validated)
                root_name = os.path.basename(scan_dir)
                _warn_if_ignore_file_missing(Path(scan_dir), ignore_file)
            structure, extensions = _scan_directory(
                Path(scan_dir),
                parsed_exclude_dirs,
                ignore_file,
                exclude_exts_set,
                parsed_exclude_patterns,
                parsed_include_patterns,
                use_regex,
                max_depth,
                show_full_path,
                spec.show_loc,
                spec.show_size,
                spec.show_mtime,
                spec.show_git_status,
            )
            if checkout is not None and show_full_path:
                apply_github_urls(structure, checkout)
            logger.info("Displaying directory tree:")
            display_tree(
                scan_dir,
                parsed_exclude_dirs,
                ignore_file,
                exclude_exts_set,
                parsed_exclude_patterns,
                parsed_include_patterns,
                use_regex,
                max_depth,
                show_full_path,
                spec,
                icon_style=resolved_style,
                structure=structure,
                extensions=extensions,
                root_name=root_name,
            )
    except GitHubError as e:
        logger.exception(f"Error: {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        raise typer.Exit(1) from None


@app.command()
def export(
    directory: str = typer.Argument(
        ".",
        help=(
            "Directory path or GitHub repository URL to export "
            "(defaults to current directory)"
        ),
    ),
    formats: list[str] = typer.Option(
        ["md"],
        "--format",
        "-f",
        help="Export formats: txt, json, html, md, svg, rst",
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
    sort_by_git_status: bool = _sort_by_git_status_option(),
    sort_by_similarity: bool = _sort_by_similarity_option(),
    loc: bool = _loc_option(),
    size: bool = _size_option(),
    mtime: bool = _mtime_option(),
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

    *directory* may also be a GitHub repository URL (optionally pinning a
    branch/tag and subtree via ``/tree/<ref>`` or ``/tree/<ref>/<subpath>``),
    in which case the
    repository is downloaded and scanned like a local directory. For a GitHub
    input the ``--ignore-file``, ``--git-status``, ``--sort-by-git-status``,
    ``--mtime`` and ``--sort-by-mtime`` options do not apply and are skipped,
    while ``--full-path`` writes each file's GitHub blob URL instead of a
    filesystem path.

    Sorting and annotation flags are resolved strictly by their left-to-right
    order on the command line: only the first sorting flag (``--sort-by-*``)
    takes effect, while every display-only flag (``--loc``, ``--size``,
    ``--mtime``, ``--git-status``) always annotates, in the order given. See
    :mod:`recursivist.flags` for the full resolution rules.

    Args:
        directory: Root directory to export, or a GitHub repository URL.
            Must exist and be a directory when local. Defaults to the current
            working directory.
        formats: Export format identifiers. Supported values are
            ``"txt"``, ``"json"``, ``"html"``, ``"md"``, ``"svg"``,
            and ``"rst"``. Multiple formats may be given as
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
            Ignored entirely if an earlier sorting flag was given.
        sort_by_size: When ``True``, sort files by size (descending)
            and annotate each file with its size. Ignored entirely if
            an earlier sorting flag was given.
        sort_by_mtime: When ``True``, sort files by last-modification
            time (newest first) and annotate each file with its
            timestamp. Ignored entirely if an earlier sorting flag was
            given.
        sort_by_git_status: When ``True``, sort files by Git status and
            annotate each file with its status marker. Ignored entirely
            if an earlier sorting flag was given.
        sort_by_similarity: When ``True``, group files with similar
            names next to each other. Ignored entirely if an earlier
            sorting flag was given.
        loc: When ``True``, display each file's lines-of-code count
            without affecting the sort order.
        size: When ``True``, display each file's size without affecting
            the sort order.
        mtime: When ``True``, display each file's modification time
            without affecting the sort order.
        show_git_status: When ``True``, annotate files with their Git
            status markers without affecting the sort order.
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
        >>> # Export a GitHub repository to Markdown with blob URLs
        >>> recursivist export https://github.com/owner/repo -f md -l
    """
    _enable_verbose_if_requested(verbose)

    resolved_style = icon_style or "emoji"
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
    )

    validated: Path = Path(directory)
    if is_remote:
        _log_ignored_remote_flags(
            ignore_file, sort_by_git_status, show_git_status, sort_by_mtime, mtime
        )
        ignore_file = None
    else:
        validated = _resolve_and_validate_directory(Path(directory))
        ignore_file = _resolve_ignore_file([validated], ignore_file)

    _log_display_options(max_depth, show_full_path, spec)
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
    try:
        with contextlib.ExitStack() as stack:
            if target is not None:
                checkout = stack.enter_context(checkout_repository(target))
                scan_dir = checkout.local_root
                root_name = checkout.root_name
                full_path_base: str | None = (
                    f"https://github.com/{target.owner}/{target.repo}"
                    if show_full_path
                    else None
                )
            else:
                checkout = None
                scan_dir = str(validated)
                root_name = os.path.basename(scan_dir)
                full_path_base = scan_dir if show_full_path else None
                _warn_if_ignore_file_missing(Path(scan_dir), ignore_file)
            structure, _ = _scan_directory(
                Path(scan_dir),
                parsed_exclude_dirs,
                ignore_file,
                exclude_exts_set,
                parsed_exclude_patterns,
                parsed_include_patterns,
                use_regex,
                max_depth,
                show_full_path,
                spec.show_loc,
                spec.show_size,
                spec.show_mtime,
                spec.show_git_status,
            )
            if checkout is not None and show_full_path:
                apply_github_urls(structure, checkout)
            parsed_formats = []
            for fmt in formats:
                parsed_formats.extend([x.strip() for x in fmt.split(" ") if x.strip()])
            valid_formats = ["txt", "json", "html", "md", "svg", "rst"]
            invalid_formats = [
                fmt for fmt in parsed_formats if fmt.lower() not in valid_formats
            ]
            if invalid_formats:
                logger.error(
                    f"Unsupported export format(s): {', '.join(invalid_formats)}"
                )
                logger.info(f"Supported formats: {', '.join(valid_formats)}")
                raise typer.Exit(1)
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(".")

            num_formats = len(parsed_formats)
            format_word = "format" if num_formats == 1 else "formats"
            logger.info(f"Exporting to {num_formats} {format_word}")
            for fmt in parsed_formats:
                output_path = output_dir / f"{output_prefix}.{fmt.lower()}"
                try:
                    exporter = get_exporter(
                        format_type=fmt.lower(),
                        structure=structure,
                        root_name=root_name,
                        base_path=full_path_base,
                        spec=spec,
                        icon_style=resolved_style,
                    )
                    exporter.export(str(output_path))
                    logger.info(f"Successfully exported to {output_path}")
                except Exception as e:
                    logger.exception(f"Failed to export to {fmt}: {e}")
    except GitHubError as e:
        logger.exception(f"Error: {e}")
        raise typer.Exit(1) from None
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
        >>> recursivist completion bash
        >>> recursivist completion zsh
        >>> recursivist completion fish
        >>> recursivist completion powershell
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
    dir1: str = typer.Argument(
        ...,
        help="First directory path or GitHub repository URL to compare",
    ),
    dir2: str = typer.Argument(
        ...,
        help="Second directory path or GitHub repository URL to compare",
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
    sort_by_git_status: bool = _sort_by_git_status_option(),
    sort_by_similarity: bool = _sort_by_similarity_option(),
    loc: bool = _loc_option(),
    size: bool = _size_option(),
    mtime: bool = _mtime_option(),
    show_git_status: bool = _show_git_status_option(),
    icon_style: str | None = _icon_style_option(
        "Override icon style. Defaults to 'emoji' if saving to HTML, else user config."
    ),
    verbose: bool = _verbose_option(),
) -> None:
    """Compare two directory structures side by side.

    Builds the tree for each input using identical filtering options,
    then renders a color-highlighted side-by-side diff. Items present
    only in *dir1* are highlighted in one color; items present only in
    *dir2* in another; shared items are shown normally. A legend is
    included in the output. When *save_as_html* is ``True`` the
    comparison is written to an HTML file instead.

    Either input may be a local directory or a GitHub repository URL
    (optionally pinning a branch/tag and subtree via
    ``/tree/<ref>`` or ``/tree/<ref>/<subpath>``), allowing a local directory
    to be compared
    against a GitHub repository, two GitHub repositories, or two local
    directories. A GitHub side is downloaded and scanned like a local
    directory, and ``--full-path`` shows its files' GitHub blob URLs. The
    ``--ignore-file``, ``--git-status`` and ``--sort-by-git-status`` options do
    not apply to a GitHub side and are skipped for it; when *both* inputs are
    GitHub repositories they are skipped entirely, but when either input is a
    local directory those options are still honored for the local side.

    Sorting and annotation flags are resolved strictly by their left-to-right
    order on the command line: only the first sorting flag (``--sort-by-*``)
    takes effect, while every display-only flag (``--loc``, ``--size``,
    ``--mtime``, ``--git-status``) always annotates, in the order given. See
    :mod:`recursivist.flags` for the full resolution rules. Git status is read
    independently for each directory, so each side is annotated against its own
    repository.

    By default, uses the persistent user configuration for icon styling
    in the terminal. If exported to HTML, strictly falls back to
    the 'emoji' style to ensure cross-platform compatibility.

    Args:
        dir1: First input to compare — a local directory path or a
            GitHub repository URL.
        dir2: Second input to compare — a local directory path or a
            GitHub repository URL.
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
            Ignored entirely if an earlier sorting flag was given.
        sort_by_size: When ``True``, sort files by size (descending)
            and annotate each file with its size. Ignored entirely if
            an earlier sorting flag was given.
        sort_by_mtime: When ``True``, sort files by last-modification
            time (newest first) and annotate each file with its
            timestamp. Ignored entirely if an earlier sorting flag was
            given.
        sort_by_git_status: When ``True``, sort files by Git status and
            annotate each file with its status marker. Ignored entirely
            if an earlier sorting flag was given.
        sort_by_similarity: When ``True``, group files with similar
            names next to each other. Ignored entirely if an earlier
            sorting flag was given.
        loc: When ``True``, display each file's lines-of-code count
            without affecting the sort order.
        size: When ``True``, display each file's size without affecting
            the sort order.
        mtime: When ``True``, display each file's modification time
            without affecting the sort order.
        show_git_status: When ``True``, annotate files with their Git status
            without affecting the sort order: ``[U]`` untracked, ``[M]``
            modified, ``[A]`` added, ``[D]`` deleted. Read independently for
            each directory.
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
        >>> # Annotate files with Git status markers
        >>> recursivist compare dir1 dir2 -G
        >>> # Sort files by Git status
        >>> recursivist compare dir1 dir2 --sort-by-git-status
        >>> # Export to HTML
        >>> recursivist compare dir1 dir2 -f
        >>> # Override icon styling
        >>> recursivist compare dir1 dir2 --icon-style nerd
        >>> # Compare a local directory against a GitHub repository
        >>> recursivist compare ./my-fork https://github.com/owner/repo
        >>> # Compare two GitHub repositories
        >>> recursivist compare https://github.com/owner/repo-a https://github.com/owner/repo-b
    """
    _enable_verbose_if_requested(verbose)

    display_dir1 = Path(dir1).resolve().name if dir1 == "." else dir1
    display_dir2 = Path(dir2).resolve().name if dir2 == "." else dir2

    logger.info(f"Comparing: {display_dir1} and {display_dir2}")

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
        if not local_dir.exists() or not local_dir.is_dir():
            logger.error(f"Error: {raw} is not a valid directory or GitHub URL")
            raise typer.Exit(1)

    if _compare_inputs_are_same(dir1, dir2, target1, target2):
        logger.error(
            f"Error: cannot compare {display_dir1} with itself; "
            "please provide two different directories or repositories"
        )
        raise typer.Exit(1)

    local_paths = [Path(raw) for raw in local_inputs]
    ignore_file = _resolve_ignore_file(local_paths, ignore_file)

    spec = resolve_display_options(
        sort_loc=sort_by_loc,
        sort_size=sort_by_size,
        sort_mtime=sort_by_mtime and not both_remote,
        sort_similarity=sort_by_similarity,
        sort_git=sort_by_git_status and not both_remote,
        disp_loc=loc,
        disp_size=size,
        disp_mtime=mtime and not both_remote,
        disp_git=show_git_status and not both_remote,
    )

    if both_remote:
        _log_ignored_remote_flags(
            ignore_file, sort_by_git_status, show_git_status, sort_by_mtime, mtime
        )
        ignore_file = None
    elif any_remote and (
        ignore_file or sort_by_git_status or show_git_status or sort_by_mtime or mtime
    ):
        logger.info(
            "Ignoring --ignore-file, --git-status, --sort-by-git-status, --mtime and "
            "--sort-by-mtime for the GitHub repository; they still apply to the local "
            "directory"
        )

    _log_display_options(max_depth, show_full_path, spec)

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
        for d in local_paths:
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
                    dir1,
                    dir2,
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
                    spec=spec,
                    icon_style=resolved_style,
                )
                logger.info(f"Successfully exported to {output_path}")
            except Exception as e:
                logger.exception(f"Failed to export to HTML: {e}")
        else:
            display_comparison(
                dir1,
                dir2,
                parsed_exclude_dirs,
                actual_ignore_file,
                exclude_exts_set,
                exclude_patterns=parsed_exclude_patterns,
                include_patterns=parsed_include_patterns,
                use_regex=use_regex,
                max_depth=max_depth,
                show_full_path=show_full_path,
                spec=spec,
                icon_style=resolved_style,
            )
    except GitHubError as e:
        logger.exception(f"Error: {e}")
        raise typer.Exit(1) from None
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
