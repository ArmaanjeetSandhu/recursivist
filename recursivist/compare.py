"""
This module contains functions to compare two directory structures and
display them side by side with highlighting of differences.
"""

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
) -> Tuple[Dict, Dict, Set[str]]:
    """
    Compare two directory structures and return both structures and a combined set of extensions.

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
) -> None:
    """
    Build a tree structure with highlighted differences.

    Args:
        structure: Dictionary representation of the current directory structure
        other_structure: Dictionary representation of the comparison directory structure
        tree: Rich Tree object to build upon
        color_map: Mapping of file extensions to colors
        parent_name: Name of the parent directory
        show_full_path: Whether to show full paths instead of just filenames
    """
    if "_files" in structure:
        files_in_other = other_structure.get("_files", []) if other_structure else []

        if (
            show_full_path
            and structure["_files"]
            and isinstance(structure["_files"][0], tuple)
        ):
            files_in_other_names = []
            for item in files_in_other:
                if isinstance(item, tuple):
                    files_in_other_names.append(item[0])
                else:
                    files_in_other_names.append(cast(str, item))

            for file_item in sort_files_by_type(structure["_files"]):
                if isinstance(file_item, tuple):
                    file_name, full_path = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")

                    if file_name not in files_in_other_names:
                        colored_text = Text(
                            f"📄 {full_path}", style=f"{color} on green"
                        )
                        tree.add(colored_text)
                    else:
                        colored_text = Text(f"📄 {full_path}", style=color)
                        tree.add(colored_text)
        else:
            for file in sort_files_by_type(structure["_files"]):
                if isinstance(file, tuple):
                    file_name, _ = file
                    ext = os.path.splitext(file_name)[1].lower()
                else:
                    file_name = cast(str, file)
                    ext = os.path.splitext(file_name)[1].lower()

                color = color_map.get(ext, "#FFFFFF")

                if file_name not in files_in_other:
                    if isinstance(file, tuple):
                        _, full_path = file
                        colored_text = Text(
                            f"📄 {full_path}", style=f"{color} on green"
                        )
                    else:
                        colored_text = Text(f"📄 {file}", style=f"{color} on green")
                    tree.add(colored_text)
                else:
                    if isinstance(file, tuple):
                        _, full_path = file
                        colored_text = Text(f"📄 {full_path}", style=color)
                    else:
                        colored_text = Text(f"📄 {file}", style=color)
                    tree.add(colored_text)

    for folder, content in sorted(structure.items()):
        if folder == "_files" or folder == "_max_depth_reached":
            continue

        other_content = other_structure.get(folder, {}) if other_structure else {}

        if folder not in (other_structure or {}):
            subtree = tree.add(Text(f"📁 {folder}", style="green"))
        else:
            subtree = tree.add(f"📁 {folder}")

        if isinstance(content, dict) and content.get("_max_depth_reached"):
            subtree.add(Text("⋯ (max depth reached)", style="dim"))
        else:
            build_comparison_tree(
                content, other_content, subtree, color_map, folder, show_full_path
            )

    if other_structure and "_files" in other_structure:
        files_in_this = structure.get("_files", [])

        if (
            show_full_path
            and other_structure["_files"]
            and isinstance(other_structure["_files"][0], tuple)
        ):
            files_in_this_names = []
            for item in files_in_this:
                if isinstance(item, tuple):
                    files_in_this_names.append(item[0])
                else:
                    files_in_this_names.append(cast(str, item))

            for file_item in sort_files_by_type(other_structure["_files"]):
                if isinstance(file_item, tuple):
                    file_name, full_path = file_item
                    if file_name not in files_in_this_names:
                        ext = os.path.splitext(file_name)[1].lower()
                        color = color_map.get(ext, "#FFFFFF")
                        colored_text = Text(f"📄 {full_path}", style=f"{color} on red")
                        tree.add(colored_text)
        else:
            for file in sort_files_by_type(other_structure["_files"]):
                if isinstance(file, tuple):
                    file_name, full_path = file
                else:
                    file_name = cast(str, file)
                    full_path = file_name

                file_in_this = False
                for this_file in files_in_this:
                    if isinstance(this_file, tuple) and this_file[0] == file_name:
                        file_in_this = True
                        break
                    elif this_file == file_name:
                        file_in_this = True
                        break

                if not file_in_this:
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(f"📄 {full_path}", style=f"{color} on red")
                    tree.add(colored_text)

    if other_structure:
        for folder in sorted(other_structure.keys()):
            if (
                folder != "_files"
                and folder != "_max_depth_reached"
                and folder not in structure
            ):
                subtree = tree.add(Text(f"📁 {folder}", style="red"))
                other_content = other_structure[folder]

                if isinstance(other_content, dict) and other_content.get(
                    "_max_depth_reached"
                ):
                    subtree.add(Text("⋯ (max depth reached)", style="dim"))
                else:
                    build_comparison_tree(
                        {}, other_content, subtree, color_map, folder, show_full_path
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
) -> None:
    """
    Display two directory trees side by side with highlighted differences.

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
    )

    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}

    console = Console()
    tree1 = Tree(Text(f"📂 {os.path.basename(dir1)}", style="bold"))
    tree2 = Tree(Text(f"📂 {os.path.basename(dir2)}", style="bold"))

    build_comparison_tree(
        structure1, structure2, tree1, color_map, show_full_path=show_full_path
    )
    build_comparison_tree(
        structure2, structure1, tree2, color_map, show_full_path=show_full_path
    )

    legend_text = Text()
    legend_text.append("Legend: ", style="bold")
    legend_text.append("Green background ", style="on green")
    legend_text.append("= Only in left directory, ")
    legend_text.append("Red background ", style="on red")
    legend_text.append("= Only in right directory")

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
) -> None:
    """
    Export directory comparison to various formats.

    Args:
        dir1: Path to the first directory
        dir2: Path to the second directory
        format_type: Export format ('txt' or 'html')
        output_path: Path where the export file will be saved
        exclude_dirs: List of directory names to exclude
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude
        exclude_patterns: List of patterns to exclude
        include_patterns: List of patterns to include (overrides exclusions)
        use_regex: Whether to treat patterns as regex instead of glob patterns
        max_depth: Maximum depth to display (0 for unlimited)
        show_full_path: Whether to show full paths instead of just filenames

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
        },
    }

    if format_type == "txt":
        _export_comparison_to_txt(comparison_data, output_path)
    elif format_type == "html":
        _export_comparison_to_html(comparison_data, output_path)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def _export_comparison_to_txt(
    comparison_data: Dict[str, Any], output_path: str
) -> None:
    """Export comparison to text format with ASCII representation."""

    def _build_txt_tree(
        structure: Dict[str, Any], prefix: str = "", is_last: bool = True
    ) -> List[str]:
        lines = []
        items = list(sorted(structure.items()))
        show_full_path = comparison_data.get("metadata", {}).get(
            "show_full_path", False
        )

        for i, (name, content) in enumerate(items):
            if name == "_files" or name == "_max_depth_reached":
                continue

            is_last_item = i == len(items) - 1 or (
                i == len(items) - 2 and "_files" in structure
            )

            if is_last_item:
                lines.append(f"{prefix}└── 📁 {name}")
                new_prefix = prefix + "    "
            else:
                lines.append(f"{prefix}├── 📁 {name}")
                new_prefix = prefix + "│   "

            if isinstance(content, dict):
                if content.get("_max_depth_reached"):
                    if is_last_item:
                        lines.append(f"{new_prefix}└── ⋯ (max depth reached)")
                    else:
                        lines.append(f"{new_prefix}├── ⋯ (max depth reached)")
                else:
                    lines.extend(_build_txt_tree(content, new_prefix, is_last_item))

        if "_files" in structure:
            files = sort_files_by_type(structure["_files"])
            for i, file_item in enumerate(files):
                is_last_file = i == len(files) - 1

                if show_full_path and isinstance(file_item, tuple):
                    _, full_path = file_item
                    display_name = full_path
                else:
                    if isinstance(file_item, tuple):
                        _, display_name = file_item
                    else:
                        display_name = cast(str, file_item)

                if is_last_file:
                    lines.append(f"{prefix}└── 📄 {display_name}")
                else:
                    lines.append(f"{prefix}├── 📄 {display_name}")

        return lines

    dir1_name = comparison_data["dir1"]["name"]
    dir2_name = comparison_data["dir2"]["name"]
    dir1_structure = comparison_data["dir1"]["structure"]
    dir2_structure = comparison_data["dir2"]["structure"]

    dir1_lines = [f"📂 {dir1_name}"]
    dir1_lines.extend(_build_txt_tree(dir1_structure))

    dir2_lines = [f"📂 {dir2_name}"]
    dir2_lines.extend(_build_txt_tree(dir2_structure))

    max_width = max(len(line) for line in dir1_lines) + 4
    combined_lines = ["Directory Comparison:"]
    combined_lines.append("=" * 80)
    combined_lines.append(f"Left: {comparison_data['dir1']['path']}")
    combined_lines.append(f"Right: {comparison_data['dir2']['path']}")

    metadata = comparison_data.get("metadata", {})
    if metadata.get("max_depth", 0) > 0:
        combined_lines.append(f"Max depth: {metadata['max_depth']} levels")

    if metadata.get("show_full_path", False):
        combined_lines.append("Showing full file paths instead of just filenames")

    if metadata.get("exclude_patterns") or metadata.get("include_patterns"):
        combined_lines.append("-" * 80)
        pattern_type = metadata.get("pattern_type", "glob")

        if metadata.get("exclude_patterns"):
            combined_lines.append(
                f"Exclude {pattern_type} patterns: {', '.join(metadata['exclude_patterns'])}"
            )

        if metadata.get("include_patterns"):
            combined_lines.append(
                f"Include {pattern_type} patterns: {', '.join(metadata['include_patterns'])}"
            )

    combined_lines.append("=" * 80)

    for i in range(max(len(dir1_lines), len(dir2_lines))):
        left = dir1_lines[i] if i < len(dir1_lines) else ""
        right = dir2_lines[i] if i < len(dir2_lines) else ""
        combined_lines.append(f"{left:<{max_width}} | {right}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(combined_lines))


def _export_comparison_to_html(
    comparison_data: Dict[str, Any], output_path: str
) -> None:
    """Export comparison to HTML format."""
    import html

    def _build_html_tree(
        structure: Dict[str, Any], include_differences: bool = False
    ) -> str:
        html_content = ["<ul>"]
        show_full_path = comparison_data.get("metadata", {}).get(
            "show_full_path", False
        )

        if "_files" in structure:
            for file_item in sort_files_by_type(structure["_files"]):
                file_class = ""
                if include_differences:
                    other_structure = (
                        comparison_data["dir2"]["structure"]
                        if structure == comparison_data["dir1"]["structure"]
                        else comparison_data["dir1"]["structure"]
                    )
                    other_files = other_structure.get("_files", [])

                    if show_full_path and isinstance(file_item, tuple):
                        file_name, full_path = file_item

                        other_file_names = []
                        for f in other_files:
                            if isinstance(f, tuple):
                                other_file_names.append(f[0])
                            else:
                                other_file_names.append(cast(str, f))

                        if file_name not in other_file_names:
                            file_class = ' class="file-unique"'

                        display_name = html.escape(full_path)
                    else:
                        if isinstance(file_item, tuple):
                            file_name, _ = file_item
                        else:
                            file_name = cast(str, file_item)

                        file_in_other = False
                        for other_file in other_files:
                            if (
                                isinstance(other_file, tuple)
                                and other_file[0] == file_name
                            ):
                                file_in_other = True
                                break
                            elif other_file == file_name:
                                file_in_other = True
                                break

                        if not file_in_other:
                            file_class = ' class="file-unique"'

                        if isinstance(file_item, tuple):
                            _, display_path = file_item
                            display_name = html.escape(display_path)
                        else:
                            display_name = html.escape(cast(str, file_item))
                else:
                    if show_full_path and isinstance(file_item, tuple):
                        _, display_path = file_item
                        display_name = html.escape(display_path)
                    else:
                        if isinstance(file_item, tuple):
                            _, display_path = file_item
                            display_name = html.escape(display_path)
                        else:
                            display_name = html.escape(cast(str, file_item))

                html_content.append(
                    f'<li{file_class}><span class="file">📄 {display_name}</span></li>'
                )

        for name, content in sorted(structure.items()):
            if name == "_files" or name == "_max_depth_reached":
                continue

            dir_class = ""
            if include_differences:
                other_structure = (
                    comparison_data["dir2"]["structure"]
                    if structure == comparison_data["dir1"]["structure"]
                    else comparison_data["dir1"]["structure"]
                )
                if name not in other_structure:
                    dir_class = ' class="directory-unique"'

            html_content.append(
                f'<li{dir_class}><span class="directory">📁 {html.escape(name)}</span>'
            )

            if isinstance(content, dict) and content.get("_max_depth_reached"):
                html_content.append(
                    '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                )
            else:
                html_content.append(_build_html_tree(content, include_differences))

            html_content.append("</li>")

        html_content.append("</ul>")
        return "\n".join(html_content)

    dir1_name = html.escape(comparison_data["dir1"]["name"])
    dir2_name = html.escape(comparison_data["dir2"]["name"])
    dir1_path = html.escape(comparison_data["dir1"]["path"])
    dir2_path = html.escape(comparison_data["dir2"]["path"])

    metadata = comparison_data.get("metadata", {})
    show_full_path = metadata.get("show_full_path", False)

    max_depth_info = ""
    if metadata.get("max_depth", 0) > 0:
        max_depth_info = f'<div class="info-block"><span class="info-label">Max Depth:</span> {metadata["max_depth"]} levels</div>'

    path_info = ""
    if show_full_path:
        path_info = '<div class="info-block"><span class="info-label">Display:</span> Showing full file paths instead of just filenames</div>'

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
            .file-unique {{
                background-color: #fcf3cf;
            }}
            .directory-unique {{
                background-color: #fcf3cf;
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
            .legend-unique {{
                background-color: #fcf3cf;
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
        {pattern_info_html}
        <div class="legend">
            <div class="legend-item">
                <span class="legend-color legend-unique"></span>
                <span>Unique to this directory</span>
            </div>
        </div>
        <div class="comparison-container">
            <div class="directory-tree">
                <h3>📂 {dir1_name}</h3>
                <p><em>Path: {dir1_path}</em></p>
                {_build_html_tree(comparison_data["dir1"]["structure"], True)}
            </div>
            <div class="directory-tree">
                <h3>📂 {dir2_name}</h3>
                <p><em>Path: {dir2_path}</em></p>
                {_build_html_tree(comparison_data["dir2"]["structure"], True)}
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
