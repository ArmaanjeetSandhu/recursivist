#!/usr/bin/env python3
"""Recursivist CLI - A beautiful directory structure visualization tool.

Provides the command-line interface for the recursivist package, letting
users visualize directory structures, export them in various formats,
compare two structures side-by-side, and generate shell completion
scripts.

Main commands:
    visualize: Display a directory structure in the terminal with rich
        formatting and optional statistics.
    export: Export a directory structure to TXT, JSON, HTML, MD, JSX,
        or SVG.
    compare: Compare two directory structures with highlighted
        differences.
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
import sys
from pathlib import Path
from re import Pattern
from typing import Optional, Union, cast

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from recursivist.compare import (
    display_comparison,
    export_comparison,
)
from recursivist.core import (
    compile_regex_patterns,
    display_tree,
    export_structure,
    get_directory_structure,
)

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
        version: Display the current version.
        completion: Generate a shell completion script.
    """

    pass


def parse_list_option(option_value: Optional[list[str]]) -> list[str]:
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


@app.command()
def visualize(
    directory: Path = typer.Argument(
        ".", help="Directory path to visualize (defaults to current directory)"
    ),
    exclude_dirs: Optional[list[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Directories to exclude (space-separated or multiple flags)",
    ),
    exclude_extensions: Optional[list[str]] = typer.Option(
        None,
        "--exclude-ext",
        "-x",
        help="File extensions to exclude (space-separated or multiple flags)",
    ),
    exclude_patterns: Optional[list[str]] = typer.Option(
        None,
        "--exclude-pattern",
        "-p",
        help="Patterns to exclude (space-separated or multiple flags)",
    ),
    include_patterns: Optional[list[str]] = typer.Option(
        None,
        "--include-pattern",
        "-i",
        help="Patterns to include (overrides exclusions, space-separated or multiple flags)",
    ),
    use_regex: bool = typer.Option(
        False,
        "--regex",
        "-r",
        help="Treat patterns as regex instead of glob patterns",
    ),
    ignore_file: Optional[str] = typer.Option(
        None, "--ignore-file", "-g", help="Ignore file to use (e.g., .gitignore)"
    ),
    max_depth: int = typer.Option(
        0, "--depth", "-d", help="Maximum depth to display (0 for unlimited)"
    ),
    show_full_path: bool = typer.Option(
        False, "--full-path", "-l", help="Show full paths instead of just filenames"
    ),
    sort_by_loc: bool = typer.Option(
        False,
        "--sort-by-loc",
        "-s",
        help="Sort files by lines of code and display LOC counts",
    ),
    sort_by_size: bool = typer.Option(
        False,
        "--sort-by-size",
        "-z",
        help="Sort files by size and display file sizes",
    ),
    sort_by_mtime: bool = typer.Option(
        False,
        "--sort-by-mtime",
        "-m",
        help="Sort files by modification time and display timestamps",
    ),
    show_git_status: bool = typer.Option(
        False,
        "--git-status",
        "-G",
        help="Annotate files with Git status markers: [U] untracked, [M] modified, [A] added, [D] deleted",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
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
        show_git_status: When ``True``, annotate files with their Git
            status: ``[U]`` untracked, ``[M]`` modified, ``[A]``
            added, ``[D]`` deleted.
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
        >>> # Show full paths
        >>> recursivist visualize -l
        >>> # Sort by LOC
        >>> recursivist visualize -s
        >>> # Sort by size
        >>> recursivist visualize -z
        >>> # Sort by mtime
        >>> recursivist visualize -m
        >>> # Git status markers
        >>> recursivist visualize -G
    """

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Error: {directory} is not a valid directory")
        raise typer.Exit(1)
    if max_depth > 0:
        logger.info(f"Limiting depth to {max_depth} levels")
    if show_full_path:
        logger.info("Showing full paths instead of just filenames")
    if sort_by_loc:
        logger.info("Sorting files by lines of code and displaying LOC counts")
    if sort_by_size:
        logger.info("Sorting files by size and displaying file sizes")
    if sort_by_mtime:
        logger.info("Sorting files by modification time and displaying timestamps")
    if show_git_status:
        logger.info("Showing Git status markers for changed files")
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
    if ignore_file:
        ignore_path = directory / ignore_file
        if ignore_path.exists():
            logger.debug(f"Using ignore file: {ignore_path}")
        else:
            logger.warning(f"Ignore file not found: {ignore_path}")
    try:
        with Progress() as progress:
            task_scan = progress.add_task(
                "[cyan]Scanning directory structure...", total=None
            )
            if use_regex:
                compiled_exclude = compile_regex_patterns(
                    parsed_exclude_patterns, use_regex
                )
                compiled_include = compile_regex_patterns(
                    parsed_include_patterns, use_regex
                )
            else:
                compiled_exclude = cast(
                    list[Union[str, Pattern[str]]], parsed_exclude_patterns
                )
                compiled_include = cast(
                    list[Union[str, Pattern[str]]], parsed_include_patterns
                )
            _, extensions = get_directory_structure(
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
            )
            progress.update(task_scan, completed=True)
            logger.debug(f"Found {len(extensions)} unique file extensions")
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
        ["md"], "--format", "-f", help="Export formats: txt, json, html, md, jsx, svg"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for exports (defaults to current directory)",
    ),
    output_prefix: Optional[str] = typer.Option(
        "structure", "--prefix", "-n", help="Prefix for exported filenames"
    ),
    exclude_dirs: Optional[list[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Directories to exclude (space-separated or multiple flags)",
    ),
    exclude_extensions: Optional[list[str]] = typer.Option(
        None,
        "--exclude-ext",
        "-x",
        help="File extensions to exclude (space-separated or multiple flags)",
    ),
    exclude_patterns: Optional[list[str]] = typer.Option(
        None,
        "--exclude-pattern",
        "-p",
        help="Patterns to exclude (space-separated or multiple flags)",
    ),
    include_patterns: Optional[list[str]] = typer.Option(
        None,
        "--include-pattern",
        "-i",
        help="Patterns to include (overrides exclusions, space-separated or multiple flags)",
    ),
    use_regex: bool = typer.Option(
        False,
        "--regex",
        "-r",
        help="Treat patterns as regex instead of glob patterns",
    ),
    ignore_file: Optional[str] = typer.Option(
        None, "--ignore-file", "-g", help="Ignore file to use (e.g., .gitignore)"
    ),
    max_depth: int = typer.Option(
        0, "--depth", "-d", help="Maximum depth to export (0 for unlimited)"
    ),
    show_full_path: bool = typer.Option(
        False, "--full-path", "-l", help="Show full paths instead of just filenames"
    ),
    sort_by_loc: bool = typer.Option(
        False,
        "--sort-by-loc",
        "-s",
        help="Sort files by lines of code and display LOC counts",
    ),
    sort_by_size: bool = typer.Option(
        False,
        "--sort-by-size",
        "-z",
        help="Sort files by size and display file sizes",
    ),
    sort_by_mtime: bool = typer.Option(
        False,
        "--sort-by-mtime",
        "-m",
        help="Sort files by modification time and display timestamps",
    ),
    show_git_status: bool = typer.Option(
        False,
        "--git-status",
        "-G",
        help="Annotate files with Git status markers: [U] untracked, [M] modified, [A] added, [D] deleted",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Export a directory structure to one or more file formats.

    Scans *directory*, builds the internal tree representation, and
    writes output files without rendering anything to the terminal.
    Multiple formats can be requested in a single invocation; each
    format produces a separate file named ``<prefix>.<format>`` inside
    *output_dir*.

    Args:
        directory: Root directory to export. Must exist and be a
            directory. Defaults to the current working directory.
        formats: Export format identifiers. Supported values are
            ``"txt"``, ``"json"``, ``"html"``, ``"md"``, ``"jsx"``,
            and ``"svg"``. Multiple formats may be given as separate
            flags or as a single space-separated string.
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
        show_git_status: When ``True``, annotate files with their Git
            status markers in the exported output.
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
        >>> # Multiple formats (separate flags)
        >>> recursivist export -f json -f md -f html
        >>> # Exclude directories
        >>> recursivist export -e node_modules .git
        >>> # Exclude file extensions
        >>> recursivist export -x .pyc .log
        >>> # Exclude glob patterns
        >>> recursivist export -p "*.test.js" "*.spec.js"
        >>> # Exclude regex patterns
        >>> recursivist export -p ".*test.*" -r
        >>> # Include overrides
        >>> recursivist export -i "src/*" "*.md"
        >>> # Limit depth to 2
        >>> recursivist export -d 2
        >>> # Show full paths
        >>> recursivist export -l
        >>> # Custom output directory
        >>> recursivist export -o ./exports
        >>> # Sort by LOC
        >>> recursivist export -s
        >>> # Sort by size
        >>> recursivist export -z
        >>> # Sort by mtime
        >>> recursivist export -m
        >>> # Git status markers
        >>> recursivist export -G
    """

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Error: {directory} is not a valid directory")
        raise typer.Exit(1)
    if max_depth > 0:
        logger.info(f"Limiting depth to {max_depth} levels")
    if show_full_path:
        logger.info("Showing full paths instead of just filenames")
    if sort_by_loc:
        logger.info("Sorting files by lines of code and displaying LOC counts")
    if sort_by_size:
        logger.info("Sorting files by size and displaying file sizes")
    if sort_by_mtime:
        logger.info("Sorting files by modification time and displaying timestamps")
    if show_git_status:
        logger.info("Annotating files with Git status markers")
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
    if ignore_file:
        ignore_path = directory / ignore_file
        if ignore_path.exists():
            logger.debug(f"Using ignore file: {ignore_path}")
        else:
            logger.warning(f"Ignore file not found: {ignore_path}")
    try:
        from recursivist.core import get_git_status as _get_git_status

        git_status_map = _get_git_status(str(directory)) if show_git_status else None
        if show_git_status and not git_status_map:
            logger.debug(
                "Git status requested but no data returned — "
                "directory may not be inside a Git repository, or there are no changes."
            )
        with Progress() as progress:
            task_scan = progress.add_task(
                "[cyan]Scanning directory structure...", total=None
            )
            if use_regex:
                compiled_exclude = compile_regex_patterns(
                    parsed_exclude_patterns, use_regex
                )
                compiled_include = compile_regex_patterns(
                    parsed_include_patterns, use_regex
                )
            else:
                compiled_exclude = cast(
                    list[Union[str, Pattern[str]]], parsed_exclude_patterns
                )
                compiled_include = cast(
                    list[Union[str, Pattern[str]]], parsed_include_patterns
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
        parsed_formats = []
        for fmt in formats:
            parsed_formats.extend([x.strip() for x in fmt.split(" ") if x.strip()])
        valid_formats = ["txt", "json", "html", "md", "jsx", "svg"]
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
                export_structure(
                    structure,
                    str(directory),
                    fmt.lower(),
                    str(output_path),
                    show_full_path,
                    sort_by_loc,
                    sort_by_size,
                    sort_by_mtime,
                    show_git_status,
                )
                logger.info(f"Successfully exported to {output_path}")
            except Exception as e:
                logger.error(f"Failed to export to {fmt}: {e}")
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
        if shell == "bash":
            completion_script = f'eval "$({sys.argv[0]} --completion-script bash)"'
        elif shell == "zsh":
            completion_script = f'eval "$({sys.argv[0]} --completion-script zsh)"'
        elif shell == "fish":
            completion_script = f"{sys.argv[0]} --completion-script fish | source"
        elif shell == "powershell":
            completion_script = f"& {sys.argv[0]} --completion-script powershell | Out-String | Invoke-Expression"
        typer.echo(completion_script)
        logger.info(f"Generated completion script for {shell}")
    except Exception as e:
        logger.error(f"Error generating completion script: {e}")
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
    exclude_dirs: Optional[list[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Directories to exclude (space-separated or multiple flags)",
    ),
    exclude_extensions: Optional[list[str]] = typer.Option(
        None,
        "--exclude-ext",
        "-x",
        help="File extensions to exclude (space-separated or multiple flags)",
    ),
    exclude_patterns: Optional[list[str]] = typer.Option(
        None,
        "--exclude-pattern",
        "-p",
        help="Patterns to exclude (space-separated or multiple flags)",
    ),
    include_patterns: Optional[list[str]] = typer.Option(
        None,
        "--include-pattern",
        "-i",
        help="Patterns to include (overrides exclusions, space-separated or multiple flags)",
    ),
    use_regex: bool = typer.Option(
        False,
        "--regex",
        "-r",
        help="Treat patterns as regex instead of glob patterns",
    ),
    ignore_file: Optional[str] = typer.Option(
        None, "--ignore-file", "-g", help="Ignore file to use (e.g., .gitignore)"
    ),
    max_depth: int = typer.Option(
        0, "--depth", "-d", help="Maximum depth to display (0 for unlimited)"
    ),
    save_as_html: bool = typer.Option(
        False,
        "--save",
        "-f",
        help="Save comparison as HTML file instead of displaying in terminal",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for exports (defaults to current directory)",
    ),
    output_prefix: Optional[str] = typer.Option(
        "comparison", "--prefix", "-n", help="Prefix for exported filenames"
    ),
    show_full_path: bool = typer.Option(
        False, "--full-path", "-l", help="Show full paths instead of just filenames"
    ),
    sort_by_loc: bool = typer.Option(
        False,
        "--sort-by-loc",
        "-s",
        help="Sort files by lines of code and display LOC counts",
    ),
    sort_by_size: bool = typer.Option(
        False,
        "--sort-by-size",
        "-z",
        help="Sort files by size and display file sizes",
    ),
    sort_by_mtime: bool = typer.Option(
        False,
        "--sort-by-mtime",
        "-m",
        help="Sort files by modification time and display timestamps",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Compare two directory structures side by side.

    Builds the tree for each directory using identical filtering
    options, then renders a color-highlighted side-by-side diff.
    Items present only in *dir1* are highlighted in one color; items
    present only in *dir2* in another; shared items are shown normally.
    A legend is included in the output. When *save_as_html* is
    ``True`` the comparison is written to an HTML file instead.

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
        >>> # HTML to custom directory
        >>> recursivist compare dir1 dir2 -f -o ./out
        >>> # Sort by LOC
        >>> recursivist compare dir1 dir2 -s
        >>> # Sort by size
        >>> recursivist compare dir1 dir2 -z
        >>> # Sort by mtime
        >>> recursivist compare dir1 dir2 -m
    """

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    logger.info(f"Comparing directories: {dir1} and {dir2}")
    if max_depth > 0:
        logger.info(f"Limiting depth to {max_depth} levels")
    if show_full_path:
        logger.info("Showing full paths instead of just filenames")
    if sort_by_loc:
        logger.info("Sorting files by lines of code and displaying LOC counts")
    if sort_by_size:
        logger.info("Sorting files by size and displaying file sizes")
    if sort_by_mtime:
        logger.info("Sorting files by modification time and displaying timestamps")
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
                )
                logger.info(f"Successfully exported to {output_path}")
            except Exception as e:
                logger.error(f"Failed to export to HTML: {e}")
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
