#!/usr/bin/env python3
"""
Recursivist CLI - A beautiful directory structure visualization tool.

This module provides the command-line interface for the recursivist package,
allowing users to visualize directory structures and export them in various formats.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from recursivist.core import display_tree, export_structure, get_directory_structure

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
    """Recursivist CLI tool for directory visualization."""
    pass


def parse_list_option(option_value: Optional[List[str]]) -> List[str]:
    """Parse a list option that may contain space-separated values.

    This allows both multiple uses of the option flag and space-separated values:
    --exclude dir1 dir2 dir3
    --exclude dir1 --exclude dir2 --exclude dir3

    Also handles file extensions with or without the leading dot:
    --exclude-ext py pyc log
    --exclude-ext .py .pyc .log

    And supports multiple export formats:
    --export txt json md
    --export txt --export json

    Args:
        option_value: List of option values, potentially with space-separated items

    Returns:
        List of individual items
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
    ignore_file: Optional[str] = typer.Option(
        None, "--ignore-file", "-i", help="Ignore file to use (e.g., .gitignore)"
    ),
    export_formats: Optional[List[str]] = typer.Option(
        None,
        "--export",
        "-f",
        help="Export formats (space-separated or multiple flags): txt, json, html, md, jsx",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for exports (defaults to current directory)",
    ),
    output_prefix: Optional[str] = typer.Option(
        "structure", "--prefix", "-p", help="Prefix for exported filenames"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Visualize a directory structure as a tree.

    This command displays the directory structure in the terminal and
    optionally exports it to various formats. You can export to multiple
    formats at once by providing space-separated formats or using multiple
    export flags.

    Examples:
        recursivist visualize                          # Display current directory
        recursivist visualize /path/to/project         # Display specific directory
        recursivist visualize -e node_modules .git     # Exclude directories
        recursivist visualize -x .pyc .log             # Exclude file extensions
        recursivist visualize -f txt json              # Export to multiple formats
        recursivist visualize -f md -o ./exports       # Export to custom directory
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    if not directory.exists() or not directory.is_dir():
        logger.error(f"Error: {directory} is not a valid directory")
        raise typer.Exit(1)

    logger.info(f"Analyzing directory: {directory}")

    parsed_exclude_dirs = parse_list_option(exclude_dirs)
    parsed_exclude_exts = parse_list_option(exclude_extensions)

    exclude_exts_set: Set[str] = set()
    if parsed_exclude_exts:
        exclude_exts_set = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in parsed_exclude_exts
        }
        logger.debug(f"Excluding extensions: {exclude_exts_set}")

    if parsed_exclude_dirs:
        logger.debug(f"Excluding directories: {parsed_exclude_dirs}")

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

            structure, extensions = get_directory_structure(
                str(directory), parsed_exclude_dirs, ignore_file, exclude_exts_set
            )

            progress.update(task_scan, completed=True)
            logger.debug(f"Found {len(extensions)} unique file extensions")

        logger.info("Displaying directory tree:")
        display_tree(str(directory), parsed_exclude_dirs, ignore_file, exclude_exts_set)

        if export_formats:
            parsed_formats = parse_list_option(export_formats)
            valid_formats = ["txt", "json", "html", "md", "jsx"]

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

            logger.info(f"Exporting to {len(parsed_formats)} format(s)")

            with Progress() as progress:
                for fmt in parsed_formats:
                    output_path = output_dir / f"{output_prefix}.{fmt.lower()}"

                    task_export = progress.add_task(
                        f"[green]Exporting to {fmt}...", total=None
                    )

                    try:
                        export_structure(
                            structure, str(directory), fmt.lower(), str(output_path)
                        )
                        progress.update(task_export, completed=True)
                        logger.info(f"Successfully exported to {output_path}")
                    except Exception as e:
                        progress.update(task_export, completed=True)
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

    This command outputs a shell script that can be sourced to enable
    command completion for the recursivist CLI.
    """
    try:
        from typer.completion import get_completion_inspect_parameters

        valid_shells = ["bash", "zsh", "fish", "powershell"]
        if shell.lower() not in valid_shells:
            logger.error(f"Unsupported shell: {shell}")
            logger.info(f"Supported shells: {', '.join(valid_shells)}")
            raise typer.Exit(1)

        try:
            completion_script = get_completion_inspect_parameters()
        except TypeError:
            completion_script = get_completion_inspect_parameters(shell)

        typer.echo(completion_script)
        logger.info(f"Generated completion script for {shell}")
    except Exception as e:
        logger.error(f"Error generating completion script: {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """Display the current version of recursivist."""
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
    ignore_file: Optional[str] = typer.Option(
        None, "--ignore-file", "-i", help="Ignore file to use (e.g., .gitignore)"
    ),
    export_formats: Optional[List[str]] = typer.Option(
        None,
        "--export",
        "-f",
        help="Export formats (space-separated or multiple flags): txt, html",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for exports (defaults to current directory)",
    ),
    output_prefix: Optional[str] = typer.Option(
        "comparison", "--prefix", "-p", help="Prefix for exported filenames"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Compare two directory structures side by side.

    This command compares two directories and displays their structures side by side,
    highlighting the differences between them. Files and directories that exist only
    in one of the structures are highlighted.

    Examples:
        recursivist compare dir1 dir2                   # Compare two directories
        recursivist compare dir1 dir2 -e node_modules   # Exclude directories
        recursivist compare dir1 dir2 -x .pyc .log      # Exclude file extensions
        recursivist compare dir1 dir2 -f txt html       # Export comparison
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    from recursivist.compare import display_comparison, export_comparison

    logger.info(f"Comparing directories: {dir1} and {dir2}")

    parsed_exclude_dirs = parse_list_option(exclude_dirs)
    parsed_exclude_exts = parse_list_option(exclude_extensions)

    exclude_exts_set: Set[str] = set()
    if parsed_exclude_exts:
        exclude_exts_set = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in parsed_exclude_exts
        }
        logger.debug(f"Excluding extensions: {exclude_exts_set}")

    if parsed_exclude_dirs:
        logger.debug(f"Excluding directories: {parsed_exclude_dirs}")

    if ignore_file:
        for d in [dir1, dir2]:
            ignore_path = d / ignore_file
            if ignore_path.exists():
                logger.debug(f"Using ignore file from {d}: {ignore_path}")
            else:
                logger.warning(f"Ignore file not found in {d}: {ignore_path}")

    try:
        display_comparison(
            str(dir1), str(dir2), parsed_exclude_dirs, ignore_file, exclude_exts_set
        )

        if export_formats:
            parsed_formats = parse_list_option(export_formats)
            valid_formats = ["txt", "html"]

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

            logger.info(f"Exporting comparison to {len(parsed_formats)} format(s)")

            with Progress() as progress:
                for fmt in parsed_formats:
                    output_path = output_dir / f"{output_prefix}.{fmt.lower()}"

                    task_export = progress.add_task(
                        f"[green]Exporting to {fmt}...", total=None
                    )

                    try:
                        export_comparison(
                            str(dir1),
                            str(dir2),
                            fmt.lower(),
                            str(output_path),
                            parsed_exclude_dirs,
                            ignore_file,
                            exclude_exts_set,
                        )
                        progress.update(task_export, completed=True)
                        logger.info(f"Successfully exported to {output_path}")
                    except Exception as e:
                        progress.update(task_export, completed=True)
                        logger.error(f"Failed to export to {fmt}: {e}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        raise typer.Exit(1)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
