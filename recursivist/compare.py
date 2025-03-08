"""
Comparison functionality for the Recursivist directory visualization tool.

This module contains functions to compare two directory structures and display them side by side with highlighting of differences. It supports:
- Side-by-side tree visualization with highlighted unique items
- Visual indicators for files/directories that exist in only one structure
- Export of comparison results to HTML for easier sharing and review
- Consistent filtering options with the main visualization features
"""

import html
import logging
import os
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union, cast

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from recursivist.core import (
    compile_regex_patterns,
    generate_color_for_extension,
    get_directory_structure,
    sort_files_by_type,
)

logger = logging.getLogger(__name__)


def compare_directory_structures(
    dir1: str,
    dir2: str,
    exclude_dirs: Optional[List[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[Set[str]] = None,
    exclude_patterns: Optional[List[Union[str, Pattern]]] = None,
    include_patterns: Optional[List[Union[str, Pattern]]] = None,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
) -> Tuple[Dict, Dict, Set[str]]:
    """
    Compare two directory structures and return both structures and a combined set of extensions.

    Performs the initial comparison by generating directory structures for both directories using the same filtering options, then combines their file extensions for consistent color mapping.

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
    )
    combined_extensions = extensions1.union(extensions2)
    return structure1, structure2, combined_extensions


def build_comparison_tree(
    structure: Dict,
    other_structure: Dict,
    tree: Tree,
    color_map: Dict[str, str],
    parent_name: str = "Root",
    show_full_path: bool = False,
    sort_by_loc: bool = False,
) -> None:
    """
    Build a tree structure with highlighted differences.

    Recursively builds a Rich tree with visual indicators for:
    - Items that exist in both structures (normal display)
    - Items unique to the current structure (green background)
    - Items unique to the comparison structure (red background)

    When sort_by_loc is True, also displays lines of code counts.

    Args:
        structure: Dictionary representation of the current directory structure
        other_structure: Dictionary representation of the comparison directory structure
        tree: Rich Tree object to build upon
        color_map: Mapping of file extensions to colors
        parent_name: Name of the parent directory
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to display lines of code counts
    """
    if "_files" in structure:
        files_in_other = other_structure.get("_files", []) if other_structure else []
        files_in_other_names = []
        for item in files_in_other:
            if isinstance(item, tuple):
                files_in_other_names.append(item[0])
            else:
                files_in_other_names.append(cast(str, item))
        for file_item in sort_files_by_type(structure["_files"], sort_by_loc):
            if isinstance(file_item, tuple):
                file_name = file_item[0]
                if sort_by_loc and len(file_item) > 2:
                    _, full_path, loc = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    if file_name not in files_in_other_names:
                        colored_text = Text(
                            f"📄 {full_path} ({loc} lines)", style=f"{color} on green"
                        )
                    else:
                        colored_text = Text(
                            f"📄 {full_path} ({loc} lines)", style=color
                        )
                    tree.add(colored_text)
                else:
                    if len(file_item) > 2:
                        _, full_path, _ = file_item
                    else:
                        _, full_path = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    if file_name not in files_in_other_names:
                        colored_text = Text(
                            f"📄 {full_path}", style=f"{color} on green"
                        )
                    else:
                        colored_text = Text(f"📄 {full_path}", style=color)
                    tree.add(colored_text)
            else:
                file_name = cast(str, file_item)
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if file_name not in files_in_other_names:
                    colored_text = Text(f"📄 {file_name}", style=f"{color} on green")
                else:
                    colored_text = Text(f"📄 {file_name}", style=color)
                tree.add(colored_text)
    for folder, content in sorted(structure.items()):
        if folder == "_files" or folder == "_max_depth_reached" or folder == "_loc":
            continue
        other_content = other_structure.get(folder, {}) if other_structure else {}
        if folder not in (other_structure or {}):
            if sort_by_loc and isinstance(content, dict) and "_loc" in content:
                folder_loc = content["_loc"]
                subtree = tree.add(
                    Text(f"📁 {folder} ({folder_loc} lines)", style="green")
                )
            else:
                subtree = tree.add(Text(f"📁 {folder}", style="green"))
        else:
            if sort_by_loc and isinstance(content, dict) and "_loc" in content:
                folder_loc = content["_loc"]
                subtree = tree.add(f"📁 {folder} ({folder_loc} lines)")
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
            )
    if other_structure and "_files" in other_structure:
        files_in_this_names = []
        files_in_this = structure.get("_files", [])
        for item in files_in_this:
            if isinstance(item, tuple):
                files_in_this_names.append(item[0])
            else:
                files_in_this_names.append(cast(str, item))
        for file_item in sort_files_by_type(other_structure["_files"], sort_by_loc):
            if isinstance(file_item, tuple):
                file_name = file_item[0]
            else:
                file_name = cast(str, file_item)
            if file_name not in files_in_this_names:
                if sort_by_loc and isinstance(file_item, tuple) and len(file_item) > 2:
                    _, display_path, loc = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(
                        f"📄 {display_path} ({loc} lines)", style=f"{color} on red"
                    )
                    tree.add(colored_text)
                elif isinstance(file_item, tuple):
                    if len(file_item) > 2:
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
                and folder not in structure
            ):
                other_content = other_structure[folder]
                if (
                    sort_by_loc
                    and isinstance(other_content, dict)
                    and "_loc" in other_content
                ):
                    folder_loc = other_content["_loc"]
                    subtree = tree.add(
                        Text(f"📁 {folder} ({folder_loc} lines)", style="red")
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
                    )


def display_comparison(
    dir1: str,
    dir2: str,
    exclude_dirs: Optional[List[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[Set[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    use_regex: bool = False,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
) -> None:
    """
    Display two directory trees side by side with highlighted differences.

    Creates a side-by-side terminal display with:
    - Two panel layout with labeled directory trees
    - Color-coded highlighting for unique items
    - Informative legend explaining the highlighting
    - Support for all filtering options
    - Optional display of lines of code counts

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
        sort_by_loc: Whether to sort by lines of code and display LOC counts
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
    )
    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}
    console = Console()
    if sort_by_loc and "_loc" in structure1:
        tree1 = Tree(
            Text(
                f"📂 {os.path.basename(dir1)} ({structure1['_loc']} lines)",
                style="bold",
            )
        )
    else:
        tree1 = Tree(Text(f"📂 {os.path.basename(dir1)}", style="bold"))
    if sort_by_loc and "_loc" in structure2:
        tree2 = Tree(
            Text(
                f"📂 {os.path.basename(dir2)} ({structure2['_loc']} lines)",
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
    )
    build_comparison_tree(
        structure2,
        structure1,
        tree2,
        color_map,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
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
    exclude_dirs: Optional[List[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[Set[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    use_regex: bool = False,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
) -> None:
    """
    Export directory comparison to HTML format.

    Creates an HTML file containing the side-by-side comparison with:
    - Highlighted differences between directories
    - Interactive, responsive layout
    - Detailed metadata about the comparison settings
    - Visual legend explaining the highlighting
    - Optional lines of code counts and sorting

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
        sort_by_loc: Whether to sort by lines of code and display LOC counts

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
        },
    }
    if format_type == "html":
        _export_comparison_to_html(comparison_data, output_path)
    else:
        raise ValueError("Only HTML format is supported for comparison export")


def _export_comparison_to_html(
    comparison_data: Dict[str, Any], output_path: str
) -> None:
    """Export comparison to HTML format.

    Internal helper function that generates an HTML file from comparison data. Creates a responsive, styled HTML document with side-by-side directory trees and highlighted differences. Supports displaying LOC counts when enabled.

    Args:
        comparison_data: Dictionary containing comparison structures and metadata
        output_path: Path where the HTML file will be saved
    """

    def _build_html_tree(
        structure: Dict[str, Any],
        other_structure: Dict[str, Any],
        is_left_tree: bool = True,
    ) -> str:
        html_content = ["<ul>"]
        show_full_path = comparison_data.get("metadata", {}).get(
            "show_full_path", False
        )
        sort_by_loc = comparison_data.get("metadata", {}).get("sort_by_loc", False)
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
            sorted_files = sort_files_by_type(files_in_this, sort_by_loc)
            for file_item in sorted_files:
                display_text = ""
                file_name = ""
                if sort_by_loc and isinstance(file_item, tuple) and len(file_item) > 2:
                    file_name, display_path, loc = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({loc} lines)"
                elif isinstance(file_item, tuple):
                    if len(file_item) > 2:
                        file_name, display_path, _ = file_item
                    else:
                        file_name, display_path = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                else:
                    file_name = cast(str, file_item)
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
            if name == "_files" or name == "_max_depth_reached" or name == "_loc":
                continue
            if name not in other_structure:
                dir_class = (
                    ' class="directory-unique-left"'
                    if is_left_tree
                    else ' class="directory-unique-right"'
                )
            else:
                dir_class = ""
            if sort_by_loc and isinstance(content, dict) and "_loc" in content:
                loc_count = content["_loc"]
                html_content.append(
                    f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines)</span>'
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
                other_structure["_files"], sort_by_loc
            )
            for file_item in sorted_other_files:
                display_text = ""
                file_name = ""
                if sort_by_loc and isinstance(file_item, tuple) and len(file_item) > 2:
                    file_name, display_path, loc = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                    display_text = f"{display_text} ({loc} lines)"
                elif isinstance(file_item, tuple):
                    if len(file_item) > 2:
                        file_name, display_path, _ = file_item
                    else:
                        file_name, display_path = file_item
                    display_text = html.escape(
                        display_path if show_full_path else file_name
                    )
                else:
                    file_name = cast(str, file_item)
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
                    or name in structure
                ):
                    continue
                dir_class = (
                    ' class="directory-unique-right"'
                    if is_left_tree
                    else ' class="directory-unique-left"'
                )
                if sort_by_loc and isinstance(content, dict) and "_loc" in content:
                    loc_count = content["_loc"]
                    html_content.append(
                        f'<li{dir_class}><span class="directory">📁 {html.escape(name)} ({loc_count} lines)</span>'
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
                    {''.join(pattern_items)}
                </dl>
            </div>
            """
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
            /* Left tree unique item - green background (like terminal) */
            .file-unique-left, .directory-unique-left {{
                background-color: #d4edda;
            }}
            /* Right tree unique item - red background (like terminal) */
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
        </style>
    </head>
    <body>
        <h1>Directory Comparison</h1>
        {max_depth_info}
        {path_info}
        {loc_info}
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
                <h3>📂 {dir1_name}{' (' + str(dir1_structure.get('_loc', 0)) + ' lines)' if metadata.get('sort_by_loc') else ''}</h3>
                <p><em>Path: {dir1_path}</em></p>
                {_build_html_tree(dir1_structure, dir2_structure, True)}
            </div>
            <div class="directory-tree">
                <h3>📂 {dir2_name}{' (' + str(dir2_structure.get('_loc', 0)) + ' lines)' if metadata.get('sort_by_loc') else ''}</h3>
                <p><em>Path: {dir2_path}</em></p>
                {_build_html_tree(dir2_structure, dir1_structure, False)}
            </div>
        </div>
    </body>
    </html>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
