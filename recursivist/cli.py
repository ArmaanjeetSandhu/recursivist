#!/usr/bin/env python3
"""
Recursivist CLI - A beautiful directory structure visualization tool.

This module provides the command-line interface for the recursivist package, allowing users to visualize directory structures, export them in various formats, compare two directory structures side by side, and handle shell completion.

The CLI is built with Typer and offers rich, colorful output through the Rich library.

Main commands:
- visualize: Display a directory structure in the terminal
- export: Export a directory structure to various file formats
- compare: Compare two directory structures with highlighted differences
- version: Display the current version information
- completion: Generate shell completion scripts
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Pattern, Set, Union, cast

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

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
def callback():
    """
    Recursivist CLI tool for directory visualization and export.

    This callback provides general information about the available commands in the Recursivist CLI tool.

    Commands:
    - visualize: Display a directory structure in the terminal
    - export: Export a directory structure to various file formats
    - compare: Compare two directory structures side by side
    - version: Display the current version
    - completion: Generate shell completion script for various shells
    """
    pass


def parse_list_option(option_value: Optional[List[str]]) -> List[str]:
    """Parse a list option that may contain space-separated values.

    Handles various input formats for CLI options, supporting both:
    - Multiple uses of the option flag: --exclude dir1 --exclude dir2
    - Space-separated values with a single flag: --exclude dir1 dir2 dir3

    Also normalizes file extensions with or without leading dots.

    Args:
        option_value: List of option values, potentially with space-separated items

    Returns:
        List of individual items with each value separated
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
    exclude_dirs: Optional[List[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Directories to exclude (space-separated or multiple flags)",
    ),
    exclude_extensions: Optional[List[str]] = typer.Option(
        None,
        "--exclude-ext",
        "-x",
        help="File extensions to exclude (space-separated or multiple flags)",
    ),
    exclude_patterns: Optional[List[str]] = typer.Option(
        None,
        "--exclude-pattern",
        "-p",
        help="Patterns to exclude (space-separated or multiple flags)",
    ),
    include_patterns: Optional[List[str]] = typer.Option(
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Visualize a directory structure as a tree in the terminal.

    Creates a rich, colorful tree visualization in the terminal with:
    - Color-coding by file extension
    - Flexible filtering options (directories, extensions, patterns)
    - Support for .gitignore files and similar
    - Depth limitation for large directories
    - Full path display option
    - Lines of code counting and sorting
    - Progress indicators for large directories

    Examples:
        recursivist visualize                             # Display current directory
        recursivist visualize /path/to/project            # Display specific directory
        recursivist visualize -e node_modules .git        # Exclude directories
        recursivist visualize -x .pyc .log                # Exclude file extensions
        recursivist visualize -p "*.test.js" "*.spec.js"  # Exclude test files (glob pattern)
        recursivist visualize -p ".*test.*" -r            # Exclude test files (regex pattern)
        recursivist visualize -i "src/*" "*.md"           # Include only src dir and markdown files
        recursivist visualize -d 2                        # Limit directory depth to 2 levels
        recursivist visualize -l                          # Show full paths instead of just filenames
        recursivist visualize -s                          # Sort by lines of code and show LOC counts
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
    parsed_exclude_dirs = parse_list_option(exclude_dirs)
    parsed_exclude_exts = parse_list_option(exclude_extensions)
    parsed_exclude_patterns = parse_list_option(exclude_patterns)
    parsed_include_patterns = parse_list_option(include_patterns)
    exclude_exts_set: Set[str] = set()
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
                    List[Union[str, Pattern[str]]], parsed_exclude_patterns
                )
                compiled_include = cast(
                    List[Union[str, Pattern[str]]], parsed_include_patterns
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
        )
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        raise typer.Exit(1)


@app.command()
def export(
    directory: Path = typer.Argument(
        ".", help="Directory path to export (defaults to current directory)"
    ),
    formats: List[str] = typer.Option(
        ["md"], "--format", "-f", help="Export formats: txt, json, html, md, jsx"
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
    exclude_dirs: Optional[List[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Directories to exclude (space-separated or multiple flags)",
    ),
    exclude_extensions: Optional[List[str]] = typer.Option(
        None,
        "--exclude-ext",
        "-x",
        help="File extensions to exclude (space-separated or multiple flags)",
    ),
    exclude_patterns: Optional[List[str]] = typer.Option(
        None,
        "--exclude-pattern",
        "-p",
        help="Patterns to exclude (space-separated or multiple flags)",
    ),
    include_patterns: Optional[List[str]] = typer.Option(
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Export a directory structure to various formats without displaying in the terminal.

    Supports multiple export formats simultaneously, with all the same filtering options as the visualization command:
    - Format options: txt, json, html, md, jsx
    - Custom output directory and filename prefix
    - Progress indicators for large directories
    - Consistent styling across formats
    - Lines of code counting and sorting

    Examples:
        recursivist export                             # Export current directory to MD
        recursivist export /path/to/project            # Export specific directory
        recursivist export -f "json md html"           # Export to multiple formats (quoted)
        recursivist export -f json -f md -f html       # Export to multiple formats (multiple flags)
        recursivist export -e node_modules .git        # Exclude directories
        recursivist export -x .pyc .log                # Exclude file extensions
        recursivist export -p "*.test.js" "*.spec.js"  # Exclude test files (glob pattern)
        recursivist export -p ".*test.*" -r            # Exclude test files (regex pattern)
        recursivist export -i "src/*" "*.md"           # Include only src dir and markdown files
        recursivist export -d 2                        # Limit directory depth to 2 levels
        recursivist export -l                          # Show full paths instead of just filenames
        recursivist export -o ./exports                # Export to custom directory
        recursivist export -s                          # Sort by lines of code and show LOC counts
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
    parsed_exclude_dirs = parse_list_option(exclude_dirs)
    parsed_exclude_exts = parse_list_option(exclude_extensions)
    parsed_exclude_patterns = parse_list_option(exclude_patterns)
    parsed_include_patterns = parse_list_option(include_patterns)
    exclude_exts_set: Set[str] = set()
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
                    List[Union[str, Pattern[str]]], parsed_exclude_patterns
                )
                compiled_include = cast(
                    List[Union[str, Pattern[str]]], parsed_include_patterns
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
            )
            progress.update(task_scan, completed=True)
            logger.debug(f"Found {len(extensions)} unique file extensions")
        parsed_formats = []
        for fmt in formats:
            parsed_formats.extend([x.strip() for x in fmt.split(" ") if x.strip()])
        valid_formats = ["txt", "json", "html", "md", "jsx"]
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
                )
                logger.info(f"Successfully exported to {output_path}")
            except Exception as e:
                logger.error(f"Failed to export to {fmt}: {e}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        raise typer.Exit(1)


@app.command()
def completion(
    shell: str = typer.Argument(..., help="Shell type (bash, zsh, fish, powershell)")
):
    """
    Generate shell completion script.

    Creates a shell-specific script that enables command completion for the recursivist CLI. The output script can be sourced to provide tab completion for commands, options, and arguments.

    Supported shells:
    - bash: Bash shell completion
    - zsh: Z shell completion
    - fish: Fish shell completion
    - powershell: PowerShell completion

    Args:
        shell: Shell type to generate completion for ('bash', 'zsh', 'fish', 'powershell')
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
        raise typer.Exit(1)


@app.command()
def version():
    """Display the current version of recursivist.

    Reads and outputs the version information from the package metadata.
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
    exclude_dirs: Optional[List[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Directories to exclude (space-separated or multiple flags)",
    ),
    exclude_extensions: Optional[List[str]] = typer.Option(
        None,
        "--exclude-ext",
        "-x",
        help="File extensions to exclude (space-separated or multiple flags)",
    ),
    exclude_patterns: Optional[List[str]] = typer.Option(
        None,
        "--exclude-pattern",
        "-p",
        help="Patterns to exclude (space-separated or multiple flags)",
    ),
    include_patterns: Optional[List[str]] = typer.Option(
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Compare two directory structures side by side.

    Creates a side-by-side comparison of two directory structures with:
    - Color highlighting for items unique to each directory
    - Same filtering options as visualization (dirs, extensions, patterns)
    - Optional export to HTML for better sharing and viewing
    - Visual legend explaining the highlighting
    - Optional sorting and display of lines of code counts

    Examples:
        recursivist compare dir1 dir2                   # Compare two directories
        recursivist compare dir1 dir2 -e node_modules   # Exclude directories
        recursivist compare dir1 dir2 -x .pyc .log      # Exclude file extensions
        recursivist compare dir1 dir2 -p "*.test.js"    # Exclude test files (glob pattern)
        recursivist compare dir1 dir2 -p ".*test.*" -r  # Exclude test files (regex pattern)
        recursivist compare dir1 dir2 -i "src/*"        # Include only src directory
        recursivist compare dir1 dir2 -d 2              # Limit directory depth to 2 levels
        recursivist compare dir1 dir2 -l                # Show full paths instead of just filenames
        recursivist compare dir1 dir2 -f                # Export comparison to HTML
        recursivist compare dir1 dir2 -s                # Sort by lines of code and show LOC counts
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    from recursivist.compare import display_comparison, export_comparison

    logger.info(f"Comparing directories: {dir1} and {dir2}")
    if max_depth > 0:
        logger.info(f"Limiting depth to {max_depth} levels")
    if show_full_path:
        logger.info("Showing full paths instead of just filenames")
    if sort_by_loc:
        logger.info("Sorting files by lines of code and displaying LOC counts")
    if sort_by_size:
        logger.info("Sorting files by size and displaying file sizes")
    parsed_exclude_dirs = parse_list_option(exclude_dirs)
    parsed_exclude_exts = parse_list_option(exclude_extensions)
    parsed_exclude_patterns = parse_list_option(exclude_patterns)
    parsed_include_patterns = parse_list_option(include_patterns)
    exclude_exts_set: Set[str] = set()
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
            )
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        raise typer.Exit(1)


def main():
    """Entry point for the CLI.

    Invokes the Typer application to process command-line arguments
    and execute the appropriate command.
    """
    app()


if __name__ == "__main__":
    main()
