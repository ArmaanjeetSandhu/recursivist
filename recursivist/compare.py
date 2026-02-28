"""
Comparison functionality for the Recursivist directory visualization tool.

This module implements side-by-side directory structure comparison with visual highlighting of differences. It provides terminal output with colored indicators and HTML export for sharing and documentation.

Key features:
- Visual highlighting of items unique to each directory
- Consistent color coding for file extensions
- Support for all the same filtering options as visualization
- Export to HTML with interactive features
- Optional display of statistics (LOC, size, modification times)
- Legend explaining the highlighting scheme
"""

import html
import logging
import os
from collections.abc import Sequence
from re import Pattern
from typing import Any, Optional, Union, cast

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from recursivist.core import (
    compile_regex_patterns,
    format_size,
    format_timestamp,
    generate_color_for_extension,
    get_directory_structure,
    sort_files_by_type,
)

logger = logging.getLogger(__name__)


def compare_directory_structures(
    dir1: str,
    dir2: str,
    exclude_dirs: Optional[Sequence[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[set[str]] = None,
    exclude_patterns: Optional[Sequence[Union[str, Pattern[str]]]] = None,
    include_patterns: Optional[Sequence[Union[str, Pattern[str]]]] = None,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], set[str]]:
    """Compare two directory structures and return both structures with a combined set of extensions.

    Retrieves the directory structures for both directories using the same filtering options, then combines their file extensions for consistent color mapping in visualizations.

    Args:
        dir1: Path to the first directory
        dir2: Path to the second directory
        exclude_dirs: List of directory names to exclude
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude
        exclude_patterns: List of patterns to exclude
        include_patterns: List of patterns to include (overrides exclusions)
        max_depth: Maximum depth to display (0 for unlimited)
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to calculate and display lines of code counts
        sort_by_size: Whether to calculate and display file sizes
        sort_by_mtime: Whether to calculate and display file modification times

    Returns:
        Tuple of (structure1, structure2, combined_extensions)
    """

    structure1, extensions1 = get_directory_structure(
        dir1,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
        max_depth=max_depth,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
    )
    structure2, extensions2 = get_directory_structure(
        dir2,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
        max_depth=max_depth,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
    )
    combined_extensions = extensions1.union(extensions2)
    return structure1, structure2, combined_extensions


def build_comparison_tree(
    structure: dict[str, Any],
    other_structure: dict[str, Any],
    tree: Tree,
    color_map: dict[str, str],
    parent_name: str = "Root",
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> None:
    """
    Build a tree structure with highlighted differences.

    Recursively builds a Rich tree with visual indicators for:
    - Items that exist in both structures (normal display)
    - Items unique to the current structure (green background)
    - Items unique to the comparison structure (red background)

    When sort_by_loc is True, also displays lines of code counts.
    When sort_by_size is True, also displays file sizes.
    When sort_by_mtime is True, also displays file modification times.

    Args:
        structure: Dictionary representation of the current directory structure
        other_structure: Dictionary representation of the comparison directory structure
        tree: Rich Tree object to build upon
        color_map: Mapping of file extensions to colors
        parent_name: Name of the parent directory
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to display lines of code counts
        sort_by_size: Whether to display file sizes
        sort_by_mtime: Whether to display file modification times
    """

    if "_files" in structure:
        files_in_other = other_structure.get("_files", []) if other_structure else []
        files_in_other_names = []
        for item in files_in_other:
            if isinstance(item, tuple):
                files_in_other_names.append(item[0])
            else:
                files_in_other_names.append(cast(str, item))
        for file_item in sort_files_by_type(
            structure["_files"], sort_by_loc, sort_by_size, sort_by_mtime
        ):
            if isinstance(file_item, tuple):
                file_name = file_item[0]
            else:
                file_name = file_item

            if (
                sort_by_loc
                and sort_by_size
                and sort_by_mtime
                and isinstance(file_item, tuple)
                and len(file_item) > 4
            ):
                file_name, full_path, loc, size, mtime = file_item
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})",
                        style=f"{color} on green",
                    )
                else:
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})",
                        style=color,
                    )
                tree.add(colored_text)
            elif (
                sort_by_loc
                and sort_by_mtime
                and isinstance(file_item, tuple)
                and len(file_item) > 3
            ):
                if len(file_item) > 4:
                    file_name, full_path, loc, _, mtime = file_item
                else:
                    file_name, full_path, loc, mtime = file_item
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines, {format_timestamp(mtime)})",
                        style=f"{color} on green",
                    )
                else:
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines, {format_timestamp(mtime)})",
                        style=color,
                    )
                tree.add(colored_text)
            elif (
                sort_by_size
                and sort_by_mtime
                and isinstance(file_item, tuple)
                and len(file_item) > 3
            ):
                if len(file_item) > 4:
                    file_name, full_path, _, size, mtime = file_item
                else:
                    file_name, full_path, size, mtime = file_item
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(
                        f"📄 {full_path} ({format_size(size)}, {format_timestamp(mtime)})",
                        style=f"{color} on green",
                    )
                else:
                    colored_text = Text(
                        f"📄 {full_path} ({format_size(size)}, {format_timestamp(mtime)})",
                        style=color,
                    )
                tree.add(colored_text)
            elif (
                sort_by_loc
                and sort_by_size
                and isinstance(file_item, tuple)
                and len(file_item) > 3
            ):
                if len(file_item) > 4:
                    file_name, full_path, loc, size, _ = file_item
                else:
                    file_name, full_path, loc, size = file_item
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines, {format_size(size)})",
                        style=f"{color} on green",
                    )
                else:
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines, {format_size(size)})",
                        style=color,
                    )
                tree.add(colored_text)
            elif sort_by_mtime and isinstance(file_item, tuple) and len(file_item) > 2:
                if len(file_item) > 4:
                    file_name, full_path, _, _, mtime = file_item
                elif len(file_item) > 3:
                    file_name, full_path, _, mtime = file_item
                else:
                    file_name, full_path, mtime = file_item
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(
                        f"📄 {full_path} ({format_timestamp(mtime)})",
                        style=f"{color} on green",
                    )
                else:
                    colored_text = Text(
                        f"📄 {full_path} ({format_timestamp(mtime)})",
                        style=color,
                    )
                tree.add(colored_text)
            elif sort_by_size and isinstance(file_item, tuple) and len(file_item) > 2:
                if len(file_item) > 3:
                    if len(file_item) > 4:
                        file_name, full_path, _, size, _ = file_item
                    else:
                        file_name, full_path, _, size = file_item
                else:
                    file_name, full_path, size = file_item
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(
                        f"📄 {full_path} ({format_size(size)})",
                        style=f"{color} on green",
                    )
                else:
                    colored_text = Text(
                        f"📄 {full_path} ({format_size(size)})",
                        style=color,
                    )
                tree.add(colored_text)
            elif sort_by_loc and isinstance(file_item, tuple) and len(file_item) > 2:
                if len(file_item) > 4:
                    file_name, full_path, loc, _, _ = file_item
                elif len(file_item) > 3:
                    file_name, full_path, loc, _ = file_item
                else:
                    file_name, full_path, loc = file_item
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines)",
                        style=f"{color} on green",
                    )
                else:
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines)",
                        style=color,
                    )
                tree.add(colored_text)
            elif isinstance(file_item, tuple):
                if len(file_item) > 4:
                    file_name, full_path, _, _, _ = file_item
                elif len(file_item) > 3:
                    file_name, full_path, _, _ = file_item
                elif len(file_item) > 2:
                    file_name, full_path, _ = file_item
                else:
                    file_name, full_path = file_item
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(f"📄 {full_path}", style=f"{color} on green")
                else:
                    colored_text = Text(f"📄 {full_path}", style=color)
                tree.add(colored_text)
            else:
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(f"📄 {file_name}", style=f"{color} on green")
                else:
                    colored_text = Text(f"📄 {file_name}", style=color)
                tree.add(colored_text)
    for folder, content in sorted(structure.items()):
        if (
            folder == "_files"
            or folder == "_max_depth_reached"
            or folder == "_loc"
            or folder == "_size"
            or folder == "_mtime"
        ):
            continue
        other_content = other_structure.get(folder, {}) if other_structure else {}
        if folder not in (other_structure or {}):
            if (
                sort_by_loc
                and sort_by_size
                and sort_by_mtime
                and isinstance(content, dict)
                and "_loc" in content
                and "_size" in content
                and "_mtime" in content
            ):
                folder_loc = content["_loc"]
                folder_size = content["_size"]
                folder_mtime = content["_mtime"]
                subtree = tree.add(
                    Text(
                        f"📁 {folder} ({folder_loc} lines, {format_size(folder_size)}, {format_timestamp(folder_mtime)})",
                        style="green",
                    )
                )
            elif (
                sort_by_loc
                and sort_by_size
                and isinstance(content, dict)
                and "_loc" in content
                and "_size" in content
            ):
                folder_loc = content["_loc"]
                folder_size = content["_size"]
                subtree = tree.add(
                    Text(
                        f"📁 {folder} ({folder_loc} lines, {format_size(folder_size)})",
                        style="green",
                    )
                )
            elif (
                sort_by_loc
                and sort_by_mtime
                and isinstance(content, dict)
                and "_loc" in content
                and "_mtime" in content
            ):
                folder_loc = content["_loc"]
                folder_mtime = content["_mtime"]
                subtree = tree.add(
                    Text(
                        f"📁 {folder} ({folder_loc} lines, {format_timestamp(folder_mtime)})",
                        style="green",
                    )
                )
            elif (
                sort_by_size
                and sort_by_mtime
                and isinstance(content, dict)
                and "_size" in content
                and "_mtime" in content
            ):
                folder_size = content["_size"]
                folder_mtime = content["_mtime"]
                subtree = tree.add(
                    Text(
                        f"📁 {folder} ({format_size(folder_size)}, {format_timestamp(folder_mtime)})",
                        style="green",
                    )
                )
            elif sort_by_loc and isinstance(content, dict) and "_loc" in content:
                folder_loc = content["_loc"]
                subtree = tree.add(
                    Text(f"📁 {folder} ({folder_loc} lines)", style="green")
                )
            elif sort_by_size and isinstance(content, dict) and "_size" in content:
                folder_size = content["_size"]
                subtree = tree.add(
                    Text(f"📁 {folder} ({format_size(folder_size)})", style="green")
                )
            elif sort_by_mtime and isinstance(content, dict) and "_mtime" in content:
                folder_mtime = content["_mtime"]
                subtree = tree.add(
                    Text(
                        f"📁 {folder} ({format_timestamp(folder_mtime)})", style="green"
                    )
                )
            else:
                subtree = tree.add(Text(f"📁 {folder}", style="green"))
        else:
            if (
                sort_by_loc
                and sort_by_size
                and sort_by_mtime
                and isinstance(content, dict)
                and "_loc" in content
                and "_size" in content
                and "_mtime" in content
            ):
                folder_loc = content["_loc"]
                folder_size = content["_size"]
                folder_mtime = content["_mtime"]
                subtree = tree.add(
                    f"📁 {folder} ({folder_loc} lines, {format_size(folder_size)}, {format_timestamp(folder_mtime)})"
                )
            elif (
                sort_by_loc
                and sort_by_size
                and isinstance(content, dict)
                and "_loc" in content
                and "_size" in content
            ):
                folder_loc = content["_loc"]
                folder_size = content["_size"]
                subtree = tree.add(
                    f"📁 {folder} ({folder_loc} lines, {format_size(folder_size)})"
                )
            elif (
                sort_by_loc
                and sort_by_mtime
                and isinstance(content, dict)
                and "_loc" in content
                and "_mtime" in content
            ):
                folder_loc = content["_loc"]
                folder_mtime = content["_mtime"]
                subtree = tree.add(
                    f"📁 {folder} ({folder_loc} lines, {format_timestamp(folder_mtime)})"
                )
            elif (
                sort_by_size
                and sort_by_mtime
                and isinstance(content, dict)
                and "_size" in content
                and "_mtime" in content
            ):
                folder_size = content["_size"]
                folder_mtime = content["_mtime"]
                subtree = tree.add(
                    f"📁 {folder} ({format_size(folder_size)}, {format_timestamp(folder_mtime)})"
                )
            elif sort_by_loc and isinstance(content, dict) and "_loc" in content:
                folder_loc = content["_loc"]
                subtree = tree.add(f"📁 {folder} ({folder_loc} lines)")
            elif sort_by_size and isinstance(content, dict) and "_size" in content:
                folder_size = content["_size"]
                subtree = tree.add(f"📁 {folder} ({format_size(folder_size)})")
            elif sort_by_mtime and isinstance(content, dict) and "_mtime" in content:
                folder_mtime = content["_mtime"]
                subtree = tree.add(f"📁 {folder} ({format_timestamp(folder_mtime)})")
            else:
                subtree = tree.add(f"📁 {folder}")
        if isinstance(content, dict) and content.get("_max_depth_reached"):
            subtree.add(Text("⋯ (max depth reached)", style="dim"))
        else:
            build_comparison_tree(
                content,
                other_content,
                subtree,
                color_map,
                folder,
                show_full_path,
                sort_by_loc,
                sort_by_size,
                sort_by_mtime,
            )
    if other_structure and "_files" in other_structure:
        files_in_this_names = []
        files_in_this = structure.get("_files", [])
        for item in files_in_this:
            if isinstance(item, tuple):
                files_in_this_names.append(item[0])
            else:
                files_in_this_names.append(cast(str, item))
        for file_item in sort_files_by_type(
            other_structure["_files"], sort_by_loc, sort_by_size, sort_by_mtime
        ):
            if isinstance(file_item, tuple):
                file_name = file_item[0]
            else:
                file_name = file_item

            if file_name not in files_in_this_names:
                if (
                    sort_by_loc
                    and sort_by_size
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 4
                ):
                    _, display_path, loc, size, mtime = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(
                        f"📄 {display_path} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})",
                        style=f"{color} on red",
                    )
                    tree.add(colored_text)
                elif (
                    sort_by_loc
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        _, display_path, loc, _, mtime = file_item
                    else:
                        _, display_path, loc, mtime = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(
                        f"📄 {display_path} ({loc} lines, {format_timestamp(mtime)})",
                        style=f"{color} on red",
                    )
                    tree.add(colored_text)
                elif (
                    sort_by_size
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        _, display_path, _, size, mtime = file_item
                    else:
                        _, display_path, size, mtime = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(
                        f"📄 {display_path} ({format_size(size)}, {format_timestamp(mtime)})",
                        style=f"{color} on red",
                    )
                    tree.add(colored_text)
                elif (
                    sort_by_loc
                    and sort_by_size
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        _, display_path, loc, size, _ = file_item
                    else:
                        _, display_path, loc, size = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(
                        f"📄 {display_path} ({loc} lines, {format_size(size)})",
                        style=f"{color} on red",
                    )
                    tree.add(colored_text)
                elif (
                    sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 2
                ):
                    if len(file_item) > 4:
                        _, full_path, _, _, mtime = file_item
                    elif len(file_item) > 3:
                        _, full_path, _, mtime = file_item
                    else:
                        _, full_path, mtime = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(
                        f"📄 {full_path} ({format_timestamp(mtime)})",
                        style=f"{color} on red",
                    )
                    tree.add(colored_text)
                elif (
                    sort_by_size and isinstance(file_item, tuple) and len(file_item) > 2
                ):
                    if len(file_item) > 3:
                        if len(file_item) > 4:
                            _, full_path, _, size, _ = file_item
                        else:
                            _, full_path, _, size = file_item
                    else:
                        _, full_path, size = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(
                        f"📄 {full_path} ({format_size(size)})",
                        style=f"{color} on red",
                    )
                    tree.add(colored_text)
                elif (
                    sort_by_loc and isinstance(file_item, tuple) and len(file_item) > 2
                ):
                    if len(file_item) > 3:
                        if len(file_item) > 4:
                            _, full_path, loc, _, _ = file_item
                        else:
                            _, full_path, loc, _ = file_item
                    else:
                        _, full_path, loc = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(
                        f"📄 {full_path} ({loc} lines)",
                        style=f"{color} on red",
                    )
                    tree.add(colored_text)
                elif isinstance(file_item, tuple):
                    if len(file_item) > 4:
                        _, full_path, _, _, _ = file_item
                    elif len(file_item) > 3:
                        _, full_path, _, _ = file_item
                    elif len(file_item) > 2:
                        _, full_path, _ = file_item
                    else:
                        _, full_path = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(f"📄 {full_path}", style=f"{color} on red")
                    tree.add(colored_text)
                else:
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(f"📄 {file_name}", style=f"{color} on red")
                    tree.add(colored_text)
    if other_structure:
        for folder in sorted(other_structure.keys()):
            if (
                folder != "_files"
                and folder != "_max_depth_reached"
                and folder != "_loc"
                and folder != "_size"
                and folder != "_mtime"
                and folder not in structure
            ):
                other_content = other_structure[folder]
                if (
                    sort_by_loc
                    and sort_by_size
                    and sort_by_mtime
                    and isinstance(other_content, dict)
                    and "_loc" in other_content
                    and "_size" in other_content
                    and "_mtime" in other_content
                ):
                    folder_loc = other_content["_loc"]
                    folder_size = other_content["_size"]
                    folder_mtime = other_content["_mtime"]
                    subtree = tree.add(
                        Text(
                            f"📁 {folder} ({folder_loc} lines, {format_size(folder_size)}, {format_timestamp(folder_mtime)})",
                            style="red",
                        )
                    )
                elif (
                    sort_by_loc
                    and sort_by_size
                    and isinstance(other_content, dict)
                    and "_loc" in other_content
                    and "_size" in other_content
                ):
                    folder_loc = other_content["_loc"]
                    folder_size = other_content["_size"]
                    subtree = tree.add(
                        Text(
                            f"📁 {folder} ({folder_loc} lines, {format_size(folder_size)})",
                            style="red",
                        )
                    )
                elif (
                    sort_by_loc
                    and sort_by_mtime
                    and isinstance(other_content, dict)
                    and "_loc" in other_content
                    and "_mtime" in other_content
                ):
                    folder_loc = other_content["_loc"]
                    folder_mtime = other_content["_mtime"]
                    subtree = tree.add(
                        Text(
                            f"📁 {folder} ({folder_loc} lines, {format_timestamp(folder_mtime)})",
                            style="red",
                        )
                    )
                elif (
                    sort_by_size
                    and sort_by_mtime
                    and isinstance(other_content, dict)
                    and "_size" in other_content
                    and "_mtime" in other_content
                ):
                    folder_size = other_content["_size"]
                    folder_mtime = other_content["_mtime"]
                    subtree = tree.add(
                        Text(
                            f"📁 {folder} ({format_size(folder_size)}, {format_timestamp(folder_mtime)})",
                            style="red",
                        )
                    )
                elif (
                    sort_by_loc
                    and isinstance(other_content, dict)
                    and "_loc" in other_content
                ):
                    folder_loc = other_content["_loc"]
                    subtree = tree.add(
                        Text(f"📁 {folder} ({folder_loc} lines)", style="red")
                    )
                elif (
                    sort_by_size
                    and isinstance(other_content, dict)
                    and "_size" in other_content
                ):
                    folder_size = other_content["_size"]
                    subtree = tree.add(
                        Text(f"📁 {folder} ({format_size(folder_size)})", style="red")
                    )
                elif (
                    sort_by_mtime
                    and isinstance(other_content, dict)
                    and "_mtime" in other_content
                ):
                    folder_mtime = other_content["_mtime"]
                    subtree = tree.add(
                        Text(
                            f"📁 {folder} ({format_timestamp(folder_mtime)})",
                            style="red",
                        )
                    )
                else:
                    subtree = tree.add(Text(f"📁 {folder}", style="red"))
                if isinstance(other_content, dict) and other_content.get(
                    "_max_depth_reached"
                ):
                    subtree.add(Text("⋯ (max depth reached)", style="dim"))
                else:
                    build_comparison_tree(
                        {},
                        other_content,
                        subtree,
                        color_map,
                        folder,
                        show_full_path,
                        sort_by_loc,
                        sort_by_size,
                        sort_by_mtime,
                    )


def display_comparison(
    dir1: str,
    dir2: str,
    exclude_dirs: Optional[list[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[set[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
    include_patterns: Optional[list[str]] = None,
    use_regex: bool = False,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> None:
    """Display two directory trees side by side with highlighted differences.

    Creates a side-by-side terminal visualization with:
    - Two panel layout with labeled directory trees
    - Color-coded highlighting for unique items (green/red background)
    - Informative legend explaining the highlighting
    - Support for all standard filtering options
    - Optional statistics display (LOC, size, modification time)

    Args:
        dir1: Path to the first directory
        dir2: Path to the second directory
        exclude_dirs: List of directory names to exclude
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude
        exclude_patterns: List of patterns to exclude
        include_patterns: List of patterns to include (overrides exclusions)
        use_regex: Whether to treat patterns as regex instead of glob patterns
        max_depth: Maximum depth to display (0 for unlimited)
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to show and sort by lines of code
        sort_by_size: Whether to show and sort by file size
        sort_by_mtime: Whether to show and sort by modification time
    """

    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_extensions is None:
        exclude_extensions = set()
    if exclude_patterns is None:
        exclude_patterns = []
    if include_patterns is None:
        include_patterns = []
    exclude_extensions = {
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in exclude_extensions
    }
    compiled_exclude = compile_regex_patterns(exclude_patterns, use_regex)
    compiled_include = compile_regex_patterns(include_patterns, use_regex)
    structure1, structure2, extensions = compare_directory_structures(
        dir1,
        dir2,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        exclude_patterns=compiled_exclude,
        include_patterns=compiled_include,
        max_depth=max_depth,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
    )
    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}
    console = Console()
    if (
        sort_by_loc
        and sort_by_size
        and sort_by_mtime
        and "_loc" in structure1
        and "_size" in structure1
        and "_mtime" in structure1
    ):
        tree1 = Tree(
            Text(
                f"📂 {os.path.basename(dir1)} ({structure1['_loc']} lines, {format_size(structure1['_size'])}, {format_timestamp(structure1['_mtime'])})",
                style="bold",
            )
        )
    elif (
        sort_by_loc and sort_by_size and "_loc" in structure1 and "_size" in structure1
    ):
        tree1 = Tree(
            Text(
                f"📂 {os.path.basename(dir1)} ({structure1['_loc']} lines, {format_size(structure1['_size'])})",
                style="bold",
            )
        )
    elif (
        sort_by_loc
        and sort_by_mtime
        and "_loc" in structure1
        and "_mtime" in structure1
    ):
        tree1 = Tree(
            Text(
                f"📂 {os.path.basename(dir1)} ({structure1['_loc']} lines, {format_timestamp(structure1['_mtime'])})",
                style="bold",
            )
        )
    elif (
        sort_by_size
        and sort_by_mtime
        and "_size" in structure1
        and "_mtime" in structure1
    ):
        tree1 = Tree(
            Text(
                f"📂 {os.path.basename(dir1)} ({format_size(structure1['_size'])}, {format_timestamp(structure1['_mtime'])})",
                style="bold",
            )
        )
    elif sort_by_loc and "_loc" in structure1:
        tree1 = Tree(
            Text(
                f"📂 {os.path.basename(dir1)} ({structure1['_loc']} lines)",
                style="bold",
            )
        )
    elif sort_by_size and "_size" in structure1:
        tree1 = Tree(
            Text(
                f"📂 {os.path.basename(dir1)} ({format_size(structure1['_size'])})",
                style="bold",
            )
        )
    elif sort_by_mtime and "_mtime" in structure1:
        tree1 = Tree(
            Text(
                f"📂 {os.path.basename(dir1)} ({format_timestamp(structure1['_mtime'])})",
                style="bold",
            )
        )
    else:
        tree1 = Tree(Text(f"📂 {os.path.basename(dir1)}", style="bold"))
    if (
        sort_by_loc
        and sort_by_size
        and sort_by_mtime
        and "_loc" in structure2
        and "_size" in structure2
        and "_mtime" in structure2
    ):
        tree2 = Tree(
            Text(
                f"📂 {os.path.basename(dir2)} ({structure2['_loc']} lines, {format_size(structure2['_size'])}, {format_timestamp(structure2['_mtime'])})",
                style="bold",
            )
        )
    elif (
        sort_by_loc and sort_by_size and "_loc" in structure2 and "_size" in structure2
    ):
        tree2 = Tree(
            Text(
                f"📂 {os.path.basename(dir2)} ({structure2['_loc']} lines, {format_size(structure2['_size'])})",
                style="bold",
            )
        )
    elif (
        sort_by_loc
        and sort_by_mtime
        and "_loc" in structure2
        and "_mtime" in structure2
    ):
        tree2 = Tree(
            Text(
                f"📂 {os.path.basename(dir2)} ({structure2['_loc']} lines, {format_timestamp(structure2['_mtime'])})",
                style="bold",
            )
        )
    elif (
        sort_by_size
        and sort_by_mtime
        and "_size" in structure2
        and "_mtime" in structure2
    ):
        tree2 = Tree(
            Text(
                f"📂 {os.path.basename(dir2)} ({format_size(structure2['_size'])}, {format_timestamp(structure2['_mtime'])})",
                style="bold",
            )
        )
    elif sort_by_loc and "_loc" in structure2:
        tree2 = Tree(
            Text(
                f"📂 {os.path.basename(dir2)} ({structure2['_loc']} lines)",
                style="bold",
            )
        )
    elif sort_by_size and "_size" in structure2:
        tree2 = Tree(
            Text(
                f"📂 {os.path.basename(dir2)} ({format_size(structure2['_size'])})",
                style="bold",
            )
        )
    elif sort_by_mtime and "_mtime" in structure2:
        tree2 = Tree(
            Text(
                f"📂 {os.path.basename(dir2)} ({format_timestamp(structure2['_mtime'])})",
                style="bold",
            )
        )
    else:
        tree2 = Tree(Text(f"📂 {os.path.basename(dir2)}", style="bold"))
    build_comparison_tree(
        structure1,
        structure2,
        tree1,
        color_map,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
    )
    build_comparison_tree(
        structure2,
        structure1,
        tree2,
        color_map,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
    )
    legend_text = Text()
    legend_text.append("Legend: ", style="bold")
    legend_text.append("Green background ", style="on green")
    legend_text.append("= In this directory, ")
    legend_text.append("Red background ", style="on red")
    legend_text.append("= In the other directory")
    if sort_by_loc:
        legend_text.append("\n")
        legend_text.append(
            "LOC counts shown in parentheses, files sorted by line count"
        )
    if sort_by_size:
        legend_text.append("\n")
        legend_text.append("File sizes shown in parentheses, files sorted by size")
    if sort_by_mtime:
        legend_text.append("\n")
        legend_text.append(
            "Modification times shown in parentheses, files sorted by newest first"
        )
    if max_depth > 0:
        legend_text.append("\n")
        legend_text.append("⋯ (max depth reached) ", style="dim")
        legend_text.append(f"= Directory tree is limited to {max_depth} levels")
    if show_full_path:
        legend_text.append("\n")
        legend_text.append("Full file paths are shown instead of just filenames")
    if exclude_patterns or include_patterns:
        pattern_info = []
        if exclude_patterns:
            pattern_type = "Regex" if use_regex else "Glob"
            pattern_info.append(
                f"{pattern_type} exclusion patterns: {', '.join(str(p) for p in exclude_patterns)}"
            )
        if include_patterns:
            pattern_type = "Regex" if use_regex else "Glob"
            pattern_info.append(
                f"{pattern_type} inclusion patterns: {', '.join(str(p) for p in include_patterns)}"
            )
        if pattern_info:
            pattern_panel = Panel(
                "\n".join(pattern_info), title="Applied Patterns", border_style="blue"
            )
            console.print(pattern_panel)
    legend_panel = Panel(legend_text, border_style="dim")
    console.print(legend_panel)
    console.print(
        Columns(
            [
                Panel(
                    tree1,
                    title=f"Directory 1: {os.path.basename(dir1)}",
                    border_style="blue",
                ),
                Panel(
                    tree2,
                    title=f"Directory 2: {os.path.basename(dir2)}",
                    border_style="green",
                ),
            ],
            equal=True,
            expand=True,
        )
    )


def export_comparison(
    dir1: str,
    dir2: str,
    format_type: str,
    output_path: str,
    exclude_dirs: Optional[list[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[set[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
    include_patterns: Optional[list[str]] = None,
    use_regex: bool = False,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> None:
    """Export directory comparison to HTML format.

    Creates an HTML file containing the side-by-side comparison with:
    - Highlighted differences between directories
    - Interactive, responsive layout
    - Detailed metadata about the comparison settings
    - Visual legend explaining the highlighting
    - Optional statistics display

    Currently only supports HTML export format.

    Args:
        dir1: Path to the first directory
        dir2: Path to the second directory
        format_type: Export format (only 'html' is supported)
        output_path: Path where the export file will be saved
        exclude_dirs: List of directory names to exclude
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude
        exclude_patterns: List of patterns to exclude
        include_patterns: List of patterns to include (overrides exclusions)
        use_regex: Whether to treat patterns as regex instead of glob patterns
        max_depth: Maximum depth to display (0 for unlimited)
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to show and sort by lines of code
        sort_by_size: Whether to show and sort by file size
        sort_by_mtime: Whether to show and sort by modification time

    Raises:
        ValueError: If the format_type is not supported
    """

    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_extensions is None:
        exclude_extensions = set()
    if exclude_patterns is None:
        exclude_patterns = []
    if include_patterns is None:
        include_patterns = []
    exclude_extensions = {
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in exclude_extensions
    }
    compiled_exclude = compile_regex_patterns(exclude_patterns, use_regex)
    compiled_include = compile_regex_patterns(include_patterns, use_regex)
    structure1, structure2, _ = compare_directory_structures(
        dir1,
        dir2,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        exclude_patterns=compiled_exclude,
        include_patterns=compiled_include,
        max_depth=max_depth,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
    )
    comparison_data = {
        "dir1": {"path": dir1, "name": os.path.basename(dir1), "structure": structure1},
        "dir2": {"path": dir2, "name": os.path.basename(dir2), "structure": structure2},
        "metadata": {
            "exclude_patterns": [str(p) for p in exclude_patterns],
            "include_patterns": [str(p) for p in include_patterns],
            "pattern_type": "regex" if use_regex else "glob",
            "max_depth": max_depth,
            "show_full_path": show_full_path,
            "sort_by_loc": sort_by_loc,
            "sort_by_size": sort_by_size,
            "sort_by_mtime": sort_by_mtime,
        },
    }
    if format_type == "html":
        _export_comparison_to_html(comparison_data, output_path)
    else:
        raise ValueError("Only HTML format is supported for comparison export")


def _export_comparison_to_html(
    comparison_data: dict[str, Any], output_path: str
) -> None:
    """Export comparison to HTML format.

    Internal helper function that generates an HTML file from comparison data. Creates a responsive, styled HTML document with side-by-side directory trees and highlighted differences. Supports displaying LOC counts, file sizes, and modification times when enabled.

    Args:
        comparison_data: Dictionary containing comparison structures and metadata
        output_path: Path where the HTML file will be saved
    """

    def _build_html_tree(
        structure: dict[str, Any],
        other_structure: dict[str, Any],
        is_left_tree: bool = True,
    ) -> str:
        """Export comparison to HTML format.

        Internal helper function that builds the HTML tree representation for each directory.
        Highlights items that only exist in one directory structure.

        Args:
            structure: Dictionary containing directory structure
            other_structure: Dictionary containing comparison directory structure
            is_left_tree: Whether this is the left tree in the comparison view

        Returns:
            HTML string representing the directory tree
        """

        html_content = ["<ul>"]
        show_full_path = comparison_data.get("metadata", {}).get(
            "show_full_path", False
        )
        sort_by_loc = comparison_data.get("metadata", {}).get("sort_by_loc", False)
        sort_by_size = comparison_data.get("metadata", {}).get("sort_by_size", False)
        sort_by_mtime = comparison_data.get("metadata", {}).get("sort_by_mtime", False)
        files_in_this = structure.get("_files", [])
        if "_files" in structure:
            files_in_other = (
                other_structure.get("_files", []) if other_structure else []
            )
            files_in_other_names = []
            for item in files_in_other:
                if isinstance(item, tuple):
                    files_in_other_names.append(item[0])
                else:
                    files_in_other_names.append(cast(str, item))
            sorted_files = sort_files_by_type(
                files_in_this, sort_by_loc, sort_by_size, sort_by_mtime
            )
            for file_item in sorted_files:
                display_text = ""
                file_name = ""
                if (
                    sort_by_loc
                    and sort_by_size
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 4
                ):
                    file_name, display_path, loc, size, mtime = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})"
                elif (
                    sort_by_loc
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        file_name, display_path, loc, _, mtime = file_item
                    else:
                        file_name, display_path, loc, mtime = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = (
                        f"{display_text} ({loc} lines, {format_timestamp(mtime)})"
                    )
                elif (
                    sort_by_size
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        file_name, display_path, _, size, mtime = file_item
                    else:
                        file_name, display_path, size, mtime = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({format_size(size)}, {format_timestamp(mtime)})"
                elif (
                    sort_by_loc
                    and sort_by_size
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        file_name, display_path, loc, size, _ = file_item
                    else:
                        file_name, display_path, loc, size = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({loc} lines, {format_size(size)})"
                elif (
                    sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 2
                ):
                    if len(file_item) > 4:
                        file_name, display_path, _, _, mtime = file_item
                    elif len(file_item) > 3:
                        file_name, display_path, _, mtime = file_item
                    else:
                        file_name, display_path, mtime = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({format_timestamp(mtime)})"
                elif (
                    sort_by_size and isinstance(file_item, tuple) and len(file_item) > 2
                ):
                    if len(file_item) > 4:
                        file_name, display_path, _, size, _ = file_item
                    elif len(file_item) > 3:
                        file_name, display_path, _, size = file_item
                    else:
                        file_name, display_path, size = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({format_size(size)})"
                elif (
                    sort_by_loc and isinstance(file_item, tuple) and len(file_item) > 2
                ):
                    if len(file_item) > 4:
                        file_name, display_path, loc, _, _ = file_item
                    elif len(file_item) > 3:
                        file_name, display_path, loc, _ = file_item
                    else:
                        file_name, display_path, loc = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({loc} lines)"
                elif isinstance(file_item, tuple):
                    if len(file_item) > 4:
                        file_name, full_path, _, _, _ = file_item
                    elif len(file_item) > 3:
                        file_name, full_path, _, _ = file_item
                    elif len(file_item) > 2:
                        file_name, full_path, _ = file_item
                    else:
                        file_name, full_path = file_item
                    display_text = html.escape(full_path)
                else:
                    file_name = file_item
                    display_text = html.escape(file_name)
                if file_name not in files_in_other_names:
                    file_class = (
                        ' class="file-unique-left"'
                        if is_left_tree
                        else ' class="file-unique-right"'
                    )
                else:
                    file_class = ""
                html_content.append(
                    f'<li{file_class}><span class="file">📄 {display_text}</span></li>'
                )
        for name, content in sorted(structure.items()):
            if (
                name == "_files"
                or name == "_max_depth_reached"
                or name == "_loc"
                or name == "_size"
                or name == "_mtime"
            ):
                continue
            if name not in other_structure:
                dir_class = (
                    ' class="directory-unique-left"'
                    if is_left_tree
                    else ' class="directory-unique-right"'
                )
            else:
                dir_class = ""
            if (
                sort_by_loc
                and sort_by_size
                and sort_by_mtime
                and isinstance(content, dict)
                and "_loc" in content
                and "_size" in content
                and "_mtime" in content
            ):
                loc_count = content["_loc"]
                size_count = content["_size"]
                mtime_count = content["_mtime"]
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines, {format_size(size_count)}, {format_timestamp(mtime_count)})</span>'
                )
            elif (
                sort_by_loc
                and sort_by_size
                and isinstance(content, dict)
                and "_loc" in content
                and "_size" in content
            ):
                loc_count = content["_loc"]
                size_count = content["_size"]
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines, {format_size(size_count)})</span>'
                )
            elif (
                sort_by_loc
                and sort_by_mtime
                and isinstance(content, dict)
                and "_loc" in content
                and "_mtime" in content
            ):
                loc_count = content["_loc"]
                mtime_count = content["_mtime"]
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines, {format_timestamp(mtime_count)})</span>'
                )
            elif (
                sort_by_size
                and sort_by_mtime
                and isinstance(content, dict)
                and "_size" in content
                and "_mtime" in content
            ):
                size_count = content["_size"]
                mtime_count = content["_mtime"]
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({format_size(size_count)}, {format_timestamp(mtime_count)})</span>'
                )
            elif sort_by_loc and isinstance(content, dict) and "_loc" in content:
                loc_count = content["_loc"]
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines)</span>'
                )
            elif sort_by_size and isinstance(content, dict) and "_size" in content:
                size_count = content["_size"]
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({format_size(size_count)})</span>'
                )
            elif sort_by_mtime and isinstance(content, dict) and "_mtime" in content:
                mtime_count = content["_mtime"]
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({format_timestamp(mtime_count)})</span>'
                )
            else:
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)}</span>'
                )
            if isinstance(content, dict) and content.get("_max_depth_reached"):
                html_content.append(
                    '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                )
            else:
                other_content = other_structure.get(name, {}) if other_structure else {}
                html_content.append(
                    _build_html_tree(content, other_content, is_left_tree)
                )
            html_content.append("</li>")
        if other_structure and "_files" in other_structure:
            files_in_this_names = []
            for item in files_in_this:
                if isinstance(item, tuple):
                    files_in_this_names.append(item[0])
                else:
                    files_in_this_names.append(cast(str, item))
            sorted_other_files = sort_files_by_type(
                other_structure["_files"], sort_by_loc, sort_by_size, sort_by_mtime
            )
            for file_item in sorted_other_files:
                display_text = ""
                file_name = ""
                if (
                    sort_by_loc
                    and sort_by_size
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 4
                ):
                    file_name, display_path, loc, size, mtime = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})"
                elif (
                    sort_by_loc
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        file_name, display_path, loc, _, mtime = file_item
                    else:
                        file_name, display_path, loc, mtime = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = (
                        f"{display_text} ({loc} lines, {format_timestamp(mtime)})"
                    )
                elif (
                    sort_by_size
                    and sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        file_name, display_path, _, size, mtime = file_item
                    else:
                        file_name, display_path, size, mtime = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({format_size(size)}, {format_timestamp(mtime)})"
                elif (
                    sort_by_loc
                    and sort_by_size
                    and isinstance(file_item, tuple)
                    and len(file_item) > 3
                ):
                    if len(file_item) > 4:
                        file_name, display_path, loc, size, _ = file_item
                    else:
                        file_name, display_path, loc, size = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({loc} lines, {format_size(size)})"
                elif (
                    sort_by_mtime
                    and isinstance(file_item, tuple)
                    and len(file_item) > 2
                ):
                    if len(file_item) > 4:
                        file_name, display_path, _, _, mtime = file_item
                    elif len(file_item) > 3:
                        file_name, display_path, _, mtime = file_item
                    else:
                        file_name, display_path, mtime = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({format_timestamp(mtime)})"
                elif (
                    sort_by_size and isinstance(file_item, tuple) and len(file_item) > 2
                ):
                    if len(file_item) > 4:
                        file_name, display_path, _, size, _ = file_item
                    elif len(file_item) > 3:
                        file_name, display_path, _, size = file_item
                    else:
                        file_name, display_path, size = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({format_size(size)})"
                elif (
                    sort_by_loc and isinstance(file_item, tuple) and len(file_item) > 2
                ):
                    if len(file_item) > 4:
                        file_name, display_path, loc, _, _ = file_item
                    elif len(file_item) > 3:
                        file_name, display_path, loc, _ = file_item
                    else:
                        file_name, display_path, loc = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({loc} lines)"
                elif isinstance(file_item, tuple):
                    if len(file_item) > 4:
                        file_name, full_path, _, _, _ = file_item
                    elif len(file_item) > 3:
                        file_name, full_path, _, _ = file_item
                    elif len(file_item) > 2:
                        file_name, full_path, _ = file_item
                    else:
                        file_name, full_path = file_item
                    display_text = html.escape(full_path)
                else:
                    file_name = file_item
                    display_text = html.escape(file_name)
                if file_name not in files_in_this_names:
                    file_class = (
                        ' class="file-unique-right"'
                        if is_left_tree
                        else ' class="file-unique-left"'
                    )
                    html_content.append(
                        f'<li{file_class}><span class="file">📄 {display_text}</span></li>'
                    )
        if other_structure:
            for name, content in sorted(other_structure.items()):
                if (
                    name == "_files"
                    or name == "_max_depth_reached"
                    or name == "_loc"
                    or name == "_size"
                    or name == "_mtime"
                    or name in structure
                ):
                    continue
                dir_class = (
                    ' class="directory-unique-right"'
                    if is_left_tree
                    else ' class="directory-unique-left"'
                )
                if (
                    sort_by_loc
                    and sort_by_size
                    and sort_by_mtime
                    and isinstance(content, dict)
                    and "_loc" in content
                    and "_size" in content
                    and "_mtime" in content
                ):
                    loc_count = content["_loc"]
                    size_count = content["_size"]
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines, {format_size(size_count)}, {format_timestamp(mtime_count)})</span>'
                    )
                elif (
                    sort_by_loc
                    and sort_by_size
                    and isinstance(content, dict)
                    and "_loc" in content
                    and "_size" in content
                ):
                    loc_count = content["_loc"]
                    size_count = content["_size"]
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines, {format_size(size_count)})</span>'
                    )
                elif (
                    sort_by_loc
                    and sort_by_mtime
                    and isinstance(content, dict)
                    and "_loc" in content
                    and "_mtime" in content
                ):
                    loc_count = content["_loc"]
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines, {format_timestamp(mtime_count)})</span>'
                    )
                elif (
                    sort_by_size
                    and sort_by_mtime
                    and isinstance(content, dict)
                    and "_size" in content
                    and "_mtime" in content
                ):
                    size_count = content["_size"]
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({format_size(size_count)}, {format_timestamp(mtime_count)})</span>'
                    )
                elif sort_by_loc and isinstance(content, dict) and "_loc" in content:
                    loc_count = content["_loc"]
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines)</span>'
                    )
                elif sort_by_size and isinstance(content, dict) and "_size" in content:
                    size_count = content["_size"]
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({format_size(size_count)})</span>'
                    )
                elif (
                    sort_by_mtime and isinstance(content, dict) and "_mtime" in content
                ):
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({format_timestamp(mtime_count)})</span>'
                    )
                else:
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)}</span>'
                    )
                if isinstance(content, dict) and content.get("_max_depth_reached"):
                    html_content.append(
                        '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                    )
                else:
                    html_content.append(_build_html_tree({}, content, is_left_tree))
                html_content.append("</li>")
        html_content.append("</ul>")
        return "\n".join(html_content)

    def format_timestamp_js() -> str:
        """Returns JavaScript function to format timestamps in HTML."""
        return """
        function formatTimestamp(timestamp) {
            const dt = new Date(timestamp * 1000);
            const now = new Date();
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            if (dt >= today) {
                return `Today ${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`;
            }
            else if (dt >= yesterday) {
                return `Yesterday ${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`;
            }
            else if ((today - dt) / (1000 * 60 * 60 * 24) < 7) {
                const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                return `${days[dt.getDay()]} ${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`;
            }
            else if (dt.getFullYear() === now.getFullYear()) {
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                return `${months[dt.getMonth()]} ${dt.getDate()}`;
            }
            else {
                return `${dt.getFullYear()}-${(dt.getMonth() + 1).toString().padStart(2, '0')}-${dt.getDate().toString().padStart(2, '0')}`;
            }
        }
        """

    dir1_name = html.escape(comparison_data["dir1"]["name"])
    dir2_name = html.escape(comparison_data["dir2"]["name"])
    dir1_path = html.escape(comparison_data["dir1"]["path"])
    dir2_path = html.escape(comparison_data["dir2"]["path"])
    dir1_structure = comparison_data["dir1"]["structure"]
    dir2_structure = comparison_data["dir2"]["structure"]
    metadata = comparison_data.get("metadata", {})
    max_depth_info = ""
    if metadata.get("max_depth", 0) > 0:
        max_depth_info = f'<div class="info-block"><span class="info-label">Max Depth:</span> {metadata["max_depth"]} levels</div>'
    path_info = ""
    if metadata.get("show_full_path"):
        path_info = '<div class="info-block"><span class="info-label">Path Display:</span> Full paths shown</div>'
    loc_info = ""
    if metadata.get("sort_by_loc"):
        loc_info = '<div class="info-block"><span class="info-label">Lines of Code:</span> Files sorted by LOC, counts displayed</div>'
    size_info = ""
    if metadata.get("sort_by_size"):
        size_info = '<div class="info-block"><span class="info-label">File Sizes:</span> Files sorted by size, sizes displayed</div>'
    mtime_info = ""
    if metadata.get("sort_by_mtime"):
        mtime_info = '<div class="info-block"><span class="info-label">Modification Times:</span> Files sorted by newest first, timestamps displayed</div>'
    pattern_info_html = ""
    if metadata.get("exclude_patterns") or metadata.get("include_patterns"):
        pattern_type = metadata.get("pattern_type", "glob").capitalize()
        pattern_items = []
        if metadata.get("exclude_patterns"):
            patterns = [html.escape(p) for p in metadata.get("exclude_patterns", [])]
            pattern_items.append(
                f"<dt>Exclude {pattern_type} Patterns:</dt><dd>{', '.join(patterns)}</dd>"
            )
        if metadata.get("include_patterns"):
            patterns = [html.escape(p) for p in metadata.get("include_patterns", [])]
            pattern_items.append(
                f"<dt>Include {pattern_type} Patterns:</dt><dd>{', '.join(patterns)}</dd>"
            )
        if pattern_items:
            pattern_info_html = f"""
            <div class="pattern-info">
                <h3>Applied Patterns</h3>
                <dl>
                    {"".join(pattern_items)}
                </dl>
            </div>
            """

    dir1_title = dir1_name
    dir2_title = dir2_name
    if (
        metadata.get("sort_by_loc")
        and metadata.get("sort_by_size")
        and metadata.get("sort_by_mtime")
    ):
        if (
            "_loc" in dir1_structure
            and "_size" in dir1_structure
            and "_mtime" in dir1_structure
        ):
            dir1_title = f"{dir1_name} ({dir1_structure['_loc']} lines, {format_size(dir1_structure['_size'])}, {format_timestamp(dir1_structure['_mtime'])})"
        if (
            "_loc" in dir2_structure
            and "_size" in dir2_structure
            and "_mtime" in dir2_structure
        ):
            dir2_title = f"{dir2_name} ({dir2_structure['_loc']} lines, {format_size(dir2_structure['_size'])}, {format_timestamp(dir2_structure['_mtime'])})"
    elif metadata.get("sort_by_loc") and metadata.get("sort_by_size"):
        if "_loc" in dir1_structure and "_size" in dir1_structure:
            dir1_title = f"{dir1_name} ({dir1_structure['_loc']} lines, {format_size(dir1_structure['_size'])})"
        if "_loc" in dir2_structure and "_size" in dir2_structure:
            dir2_title = f"{dir2_name} ({dir2_structure['_loc']} lines, {format_size(dir2_structure['_size'])})"
    elif metadata.get("sort_by_loc") and metadata.get("sort_by_mtime"):
        if "_loc" in dir1_structure and "_mtime" in dir1_structure:
            dir1_title = f"{dir1_name} ({dir1_structure['_loc']} lines, {format_timestamp(dir1_structure['_mtime'])})"
        if "_loc" in dir2_structure and "_mtime" in dir2_structure:
            dir2_title = f"{dir2_name} ({dir2_structure['_loc']} lines, {format_timestamp(dir2_structure['_mtime'])})"
    elif metadata.get("sort_by_size") and metadata.get("sort_by_mtime"):
        if "_size" in dir1_structure and "_mtime" in dir1_structure:
            dir1_title = f"{dir1_name} ({format_size(dir1_structure['_size'])}, {format_timestamp(dir1_structure['_mtime'])})"
        if "_size" in dir2_structure and "_mtime" in dir2_structure:
            dir2_title = f"{dir2_name} ({format_size(dir2_structure['_size'])}, {format_timestamp(dir2_structure['_mtime'])})"
    elif metadata.get("sort_by_loc"):
        if "_loc" in dir1_structure:
            dir1_title = f"{dir1_name} ({dir1_structure['_loc']} lines)"
        if "_loc" in dir2_structure:
            dir2_title = f"{dir2_name} ({dir2_structure['_loc']} lines)"
    elif metadata.get("sort_by_size"):
        if "_size" in dir1_structure:
            dir1_title = f"{dir1_name} ({format_size(dir1_structure['_size'])})"
        if "_size" in dir2_structure:
            dir2_title = f"{dir2_name} ({format_size(dir2_structure['_size'])})"
    elif metadata.get("sort_by_mtime"):
        if "_mtime" in dir1_structure:
            dir1_title = f"{dir1_name} ({format_timestamp(dir1_structure['_mtime'])})"
        if "_mtime" in dir2_structure:
            dir2_title = f"{dir2_name} ({format_timestamp(dir2_structure['_mtime'])})"
    js_format_timestamp = ""
    if metadata.get("sort_by_mtime"):
        js_format_timestamp = format_timestamp_js()
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Directory Comparison - {dir1_name} vs {dir2_name}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
            }}
            .comparison-container {{
                display: flex;
                border: 1px solid #ccc;
            }}
            .directory-tree {{
                flex: 1;
                padding: 15px;
                overflow: auto;
                border-right: 1px solid #ccc;
            }}
            .directory-tree:last-child {{
                border-right: none;
            }}
            h1, h2 {{
                text-align: center;
            }}
            h3 {{
                margin-top: 0;
                padding: 10px;
                background-color: #f0f0f0;
                border-bottom: 1px solid #ccc;
            }}
            ul {{
                list-style-type: none;
                padding-left: 20px;
            }}
            .directory {{
                color: #2c3e50;
                font-weight: bold;
            }}
            .file {{
                color: #34495e;
            }}
            .file-unique-left, .directory-unique-left {{
                background-color: #d4edda;
            }}
            .file-unique-right, .directory-unique-right {{
                background-color: #f8d7da;
            }}
            .max-depth {{
                color: #999;
                font-style: italic;
            }}
            .legend {{
                margin-bottom: 20px;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .legend-item {{
                display: inline-block;
                margin-right: 20px;
            }}
            .legend-color {{
                display: inline-block;
                width: 15px;
                height: 15px;
                margin-right: 5px;
                vertical-align: middle;
            }}
            .legend-left {{
                background-color: #d4edda;
            }}
            .legend-right {{
                background-color: #f8d7da;
            }}
            .pattern-info {{
                margin-bottom: 20px;
                padding: 10px;
                background-color: #f0f8ff;
                border: 1px solid #add8e6;
                border-radius: 4px;
            }}
            .info-block {{
                margin-bottom: 10px;
                color: #333;
            }}
            .info-label {{
                font-weight: bold;
            }}
            dt {{
                font-weight: bold;
                margin-top: 10px;
            }}
            dd {{
                margin-left: 20px;
                margin-bottom: 10px;
            }}
            .timestamp {{
                color: #6c757d;
                font-size: 0.9em;
            }}
        </style>
        <script>
            {js_format_timestamp}
        </script>
    </head>
    <body>
        <h1>Directory Comparison</h1>
        {max_depth_info}
        {path_info}
        {loc_info}
        {size_info}
        {mtime_info}
        {pattern_info_html}
        <div class="legend">
            <div class="legend-item">
                <span class="legend-color legend-left"></span>
                <span>In this directory</span>
            </div>
            <div class="legend-item">
                <span class="legend-color legend-right"></span>
                <span>In the other directory</span>
            </div>
        </div>
        <div class="comparison-container">
            <div class="directory-tree">
                <h3>📂 {dir1_title}</h3>
                <p><em>Path: {dir1_path}</em></p>
                {_build_html_tree(dir1_structure, dir2_structure, True)}
            </div>
            <div class="directory-tree">
                <h3>📂 {dir2_title}</h3>
                <p><em>Path: {dir2_path}</em></p>
                {_build_html_tree(dir2_structure, dir1_structure, False)}
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
