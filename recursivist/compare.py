"""Side-by-side directory comparison.

Builds the structures for two directories with identical filtering and renders
them next to each other, highlighting entries unique to either side. Supports
the same filtering and metric options as the single-tree renderer, with
terminal output for interactive use and HTML export for sharing.
"""

import html
import logging
import os
from collections.abc import Sequence
from re import Pattern
from typing import Any, cast

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from recursivist.colors import generate_color_for_extension
from recursivist.filtering import compile_regex_patterns
from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics, format_metrics_suffix
from recursivist.scanner import get_directory_structure, iter_subdirectories
from recursivist.sorting import sort_files_by_type

logger = logging.getLogger(__name__)


def compare_directory_structures(
    dir1: str,
    dir2: str,
    exclude_dirs: Sequence[str] | None = None,
    ignore_file: str | None = None,
    exclude_extensions: set[str] | None = None,
    exclude_patterns: Sequence[str | Pattern[str]] | None = None,
    include_patterns: Sequence[str | Pattern[str]] | None = None,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], set[str]]:
    """Scan two directories for comparison using identical options.

    Each directory is scanned with the same filtering and metric settings, and
    their extension sets are merged so that a single color map can be shared
    across both trees.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor (e.g. ``.gitignore``).
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include, which
            override the exclusions.
        max_depth: Maximum depth to scan, or ``0`` for unlimited.
        show_full_path: Whether to store absolute paths instead of bare
            filenames.
        sort_by_loc: Whether to count lines of code.
        sort_by_size: Whether to measure file sizes.
        sort_by_mtime: Whether to record modification times.

    Returns:
        A ``(structure1, structure2, combined_extensions)`` tuple, pairing each
        directory's structure with the union of their file extensions.
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
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
    icon_style: str = "emoji",
    sort_by_similarity: bool = False,
) -> None:
    """Populate a ``rich`` tree, highlighting differences against another tree.

    Recursively adds the entries of *structure* to *tree*, comparing each
    against *other_structure*: items present in both are shown normally, items
    unique to *structure* are highlighted in green, and items unique to
    *other_structure* are highlighted in red. Metric annotations are appended
    when the corresponding sort flag is set.

    Args:
        structure: Structure of the directory being rendered.
        other_structure: Structure of the directory being compared against.
        tree: ``rich`` tree to add nodes to. Modified in place.
        color_map: Mapping of lowercase file extension to hex color.
        show_full_path: Whether to display absolute paths instead of bare
            filenames.
        sort_by_loc: Whether to display lines-of-code counts.
        sort_by_size: Whether to display file sizes.
        sort_by_mtime: Whether to display modification times.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        sort_by_similarity: Whether to group files by name similarity.
    """
    if "_files" in structure:
        files_in_other = other_structure.get("_files", []) if other_structure else []
        files_in_other_names = []
        for item in files_in_other:
            if isinstance(item, tuple):
                files_in_other_names.append(item[0])
            else:
                files_in_other_names.append(cast(str, item))
        for entry in sort_files_by_type(
            structure["_files"],
            sort_by_loc,
            sort_by_size,
            sort_by_mtime,
            sort_by_similarity,
        ):
            file_icon = get_icon(entry.name, is_dir=False, style=icon_style)
            ext = os.path.splitext(entry.name)[1].lower()
            color = color_map.get(ext, "#FFFFFF")
            label = f"{file_icon} {entry.path}" + format_metrics_suffix(
                entry.loc,
                entry.size,
                entry.mtime,
                sort_by_loc=sort_by_loc,
                sort_by_size=sort_by_size,
                sort_by_mtime=sort_by_mtime,
            )
            style = (
                f"{color} on green" if entry.name not in files_in_other_names else color
            )
            tree.add(Text(label, style=style))
    for folder, content in iter_subdirectories(structure):
        folder_icon = get_icon(folder, is_dir=True, style=icon_style)

        other_content = other_structure.get(folder, {}) if other_structure else {}
        metrics = format_dir_metrics(
            content,
            sort_by_loc=sort_by_loc,
            sort_by_size=sort_by_size,
            sort_by_mtime=sort_by_mtime,
        )
        folder_label = f"{folder_icon} {folder}{metrics}"
        if folder not in (other_structure or {}):
            subtree = tree.add(Text(folder_label, style="green"))
        else:
            subtree = tree.add(folder_label)
        if isinstance(content, dict) and content.get("_max_depth_reached"):
            subtree.add(Text("⋯ (max depth reached)", style="dim"))
        else:
            build_comparison_tree(
                content,
                other_content,
                subtree,
                color_map,
                show_full_path,
                sort_by_loc,
                sort_by_size,
                sort_by_mtime,
                icon_style=icon_style,
                sort_by_similarity=sort_by_similarity,
            )
    if other_structure and "_files" in other_structure:
        files_in_this_names = []
        files_in_this = structure.get("_files", [])
        for item in files_in_this:
            if isinstance(item, tuple):
                files_in_this_names.append(item[0])
            else:
                files_in_this_names.append(cast(str, item))
        for entry in sort_files_by_type(
            other_structure["_files"],
            sort_by_loc,
            sort_by_size,
            sort_by_mtime,
            sort_by_similarity,
        ):
            if entry.name not in files_in_this_names:
                file_icon = get_icon(entry.name, is_dir=False, style=icon_style)
                ext = os.path.splitext(entry.name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                label = f"{file_icon} {entry.path}" + format_metrics_suffix(
                    entry.loc,
                    entry.size,
                    entry.mtime,
                    sort_by_loc=sort_by_loc,
                    sort_by_size=sort_by_size,
                    sort_by_mtime=sort_by_mtime,
                )
                tree.add(Text(label, style=f"{color} on red"))
    if other_structure:
        for folder, other_content in iter_subdirectories(other_structure):
            if folder in structure:
                continue
            folder_icon = get_icon(folder, is_dir=True, style=icon_style)

            metrics = format_dir_metrics(
                other_content,
                sort_by_loc=sort_by_loc,
                sort_by_size=sort_by_size,
                sort_by_mtime=sort_by_mtime,
            )
            subtree = tree.add(Text(f"{folder_icon} {folder}{metrics}", style="red"))
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
                    show_full_path,
                    sort_by_loc,
                    sort_by_size,
                    sort_by_mtime,
                    icon_style=icon_style,
                    sort_by_similarity=sort_by_similarity,
                )


def display_comparison(
    dir1: str,
    dir2: str,
    exclude_dirs: list[str] | None = None,
    ignore_file: str | None = None,
    exclude_extensions: set[str] | None = None,
    exclude_patterns: list[str] | None = None,
    include_patterns: list[str] | None = None,
    use_regex: bool = False,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
    icon_style: str = "emoji",
    sort_by_similarity: bool = False,
) -> None:
    """Render two directory trees side by side in the terminal.

    Scans both directories with identical options and prints them as two
    labeled, color-highlighted panels: entries unique to *dir1* and *dir2* are
    highlighted in contrasting colors, shared entries are shown normally, and a
    legend explains the scheme.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor (e.g. ``.gitignore``).
        exclude_extensions: File extensions to exclude. Normalized to a
            lowercase, dot-prefixed form before scanning.
        exclude_patterns: Glob or regex patterns to exclude.
        include_patterns: Glob or regex patterns to include, which override
            the exclusions.
        use_regex: Whether to treat the patterns as regular expressions
            instead of glob patterns.
        max_depth: Maximum depth to display, or ``0`` for unlimited.
        show_full_path: Whether to display absolute paths instead of bare
            filenames.
        sort_by_loc: Whether to display and sort by lines of code.
        sort_by_size: Whether to display and sort by file size.
        sort_by_mtime: Whether to display and sort by modification time.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        sort_by_similarity: Whether to group files by name similarity.
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

    root_base1 = os.path.basename(dir1)
    root_base2 = os.path.basename(dir2)
    root_icon1 = get_icon(root_base1, is_dir=True, style=icon_style)
    root_icon2 = get_icon(root_base2, is_dir=True, style=icon_style)

    tree1 = Tree(
        Text(
            f"{root_icon1} {root_base1}"
            + format_metrics_suffix(
                structure1.get("_loc", 0),
                structure1.get("_size", 0),
                structure1.get("_mtime", 0.0),
                sort_by_loc=sort_by_loc and "_loc" in structure1,
                sort_by_size=sort_by_size and "_size" in structure1,
                sort_by_mtime=sort_by_mtime and "_mtime" in structure1,
            ),
            style="bold",
        )
    )

    tree2 = Tree(
        Text(
            f"{root_icon2} {root_base2}"
            + format_metrics_suffix(
                structure2.get("_loc", 0),
                structure2.get("_size", 0),
                structure2.get("_mtime", 0.0),
                sort_by_loc=sort_by_loc and "_loc" in structure2,
                sort_by_size=sort_by_size and "_size" in structure2,
                sort_by_mtime=sort_by_mtime and "_mtime" in structure2,
            ),
            style="bold",
        )
    )

    build_comparison_tree(
        structure1,
        structure2,
        tree1,
        color_map,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
        icon_style=icon_style,
        sort_by_similarity=sort_by_similarity,
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
        icon_style=icon_style,
        sort_by_similarity=sort_by_similarity,
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
    if sort_by_similarity and not (sort_by_loc or sort_by_size or sort_by_mtime):
        legend_text.append("\n")
        legend_text.append("Files grouped by name similarity")
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
                    title=f"Directory 1: {root_base1}",
                    border_style="blue",
                ),
                Panel(
                    tree2,
                    title=f"Directory 2: {root_base2}",
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
    exclude_dirs: list[str] | None = None,
    ignore_file: str | None = None,
    exclude_extensions: set[str] | None = None,
    exclude_patterns: list[str] | None = None,
    include_patterns: list[str] | None = None,
    use_regex: bool = False,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
    icon_style: str = "emoji",
    sort_by_similarity: bool = False,
) -> None:
    """Export a side-by-side directory comparison to an HTML file.

    Scans both directories with identical options and writes a standalone,
    responsive HTML document containing the highlighted comparison, a legend,
    and a summary of the settings used. Only HTML output is supported.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.
        format_type: Export format. Only ``"html"`` is supported.
        output_path: Path the HTML file is written to.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor (e.g. ``.gitignore``).
        exclude_extensions: File extensions to exclude. Normalized to a
            lowercase, dot-prefixed form before scanning.
        exclude_patterns: Glob or regex patterns to exclude.
        include_patterns: Glob or regex patterns to include, which override
            the exclusions.
        use_regex: Whether to treat the patterns as regular expressions
            instead of glob patterns.
        max_depth: Maximum depth to include, or ``0`` for unlimited.
        show_full_path: Whether to write absolute paths instead of bare
            filenames.
        sort_by_loc: Whether to display and sort by lines of code.
        sort_by_size: Whether to display and sort by file size.
        sort_by_mtime: Whether to display and sort by modification time.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        sort_by_similarity: Whether to group files by name similarity.

    Raises:
        ValueError: If *format_type* is not ``"html"``.
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
            "sort_by_similarity": sort_by_similarity,
        },
    }
    if format_type == "html":
        _export_comparison_to_html(comparison_data, output_path, icon_style)
    else:
        raise ValueError("Only HTML format is supported for comparison export")


def _export_comparison_to_html(
    comparison_data: dict[str, Any], output_path: str, icon_style: str = "emoji"
) -> None:
    """Write the comparison HTML document from prepared comparison data.

    Generates a responsive, styled HTML page with the two directory trees side
    by side and their differences highlighted, including any LOC, size, or
    modification-time annotations enabled in the metadata.

    Args:
        comparison_data: Prepared comparison payload holding each directory's
            structure under ``"dir1"``/``"dir2"`` and the render settings under
            ``"metadata"``.
        output_path: Path the HTML file is written to.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
    """

    def _build_html_tree(
        structure: dict[str, Any],
        other_structure: dict[str, Any],
    ) -> str:
        """Build the nested ``<ul>`` markup for one side of the comparison.

        Walks *structure*, emitting list items for its files and
        subdirectories and tagging any entry absent from *other_structure* so
        it can be highlighted as unique.

        Args:
            structure: Structure of the directory being rendered.
            other_structure: Structure of the directory being compared against.

        Returns:
            An HTML fragment representing the directory tree.
        """
        html_content = ["<ul>"]
        show_full_path = comparison_data.get("metadata", {}).get(
            "show_full_path", False
        )
        sort_by_loc = comparison_data.get("metadata", {}).get("sort_by_loc", False)
        sort_by_size = comparison_data.get("metadata", {}).get("sort_by_size", False)
        sort_by_mtime = comparison_data.get("metadata", {}).get("sort_by_mtime", False)
        sort_by_similarity = comparison_data.get("metadata", {}).get(
            "sort_by_similarity", False
        )
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
                files_in_this,
                sort_by_loc,
                sort_by_size,
                sort_by_mtime,
                sort_by_similarity,
            )
            for entry in sorted_files:
                if sort_by_loc or sort_by_size or sort_by_mtime:
                    base = entry.path if show_full_path else entry.name
                else:
                    base = entry.path
                display_text = html.escape(base) + format_metrics_suffix(
                    entry.loc,
                    entry.size,
                    entry.mtime,
                    sort_by_loc=sort_by_loc,
                    sort_by_size=sort_by_size,
                    sort_by_mtime=sort_by_mtime,
                )
                if entry.name not in files_in_other_names:
                    file_class = ' class="file-unique-left"'
                else:
                    file_class = ""
                file_icon = get_icon(entry.name, is_dir=False, style=icon_style)
                html_content.append(
                    f'<li{file_class}><span class="file">{file_icon} {display_text}</span></li>'
                )
        for name, content in iter_subdirectories(structure):
            if name not in other_structure:
                dir_class = ' class="directory-unique-left"'
            else:
                dir_class = ""

            folder_icon = get_icon(name, is_dir=True, style=icon_style)

            metrics = format_dir_metrics(
                content,
                sort_by_loc=sort_by_loc,
                sort_by_size=sort_by_size,
                sort_by_mtime=sort_by_mtime,
            )
            html_content.append(
                f'<li{dir_class}><span class="directory">{folder_icon} '
                f"{html.escape(name)}{metrics}</span>"
            )
            if isinstance(content, dict) and content.get("_max_depth_reached"):
                html_content.append(
                    '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                )
            else:
                other_content = other_structure.get(name, {}) if other_structure else {}
                html_content.append(_build_html_tree(content, other_content))
            html_content.append("</li>")
        if other_structure and "_files" in other_structure:
            files_in_this_names = []
            for item in files_in_this:
                if isinstance(item, tuple):
                    files_in_this_names.append(item[0])
                else:
                    files_in_this_names.append(cast(str, item))
            sorted_other_files = sort_files_by_type(
                other_structure["_files"],
                sort_by_loc,
                sort_by_size,
                sort_by_mtime,
                sort_by_similarity,
            )
            for entry in sorted_other_files:
                if entry.name not in files_in_this_names:
                    if sort_by_loc or sort_by_size or sort_by_mtime:
                        base = entry.path if show_full_path else entry.name
                    else:
                        base = entry.path
                    display_text = html.escape(base) + format_metrics_suffix(
                        entry.loc,
                        entry.size,
                        entry.mtime,
                        sort_by_loc=sort_by_loc,
                        sort_by_size=sort_by_size,
                        sort_by_mtime=sort_by_mtime,
                    )
                    file_class = ' class="file-unique-right"'
                    file_icon = get_icon(entry.name, is_dir=False, style=icon_style)
                    html_content.append(
                        f'<li{file_class}><span class="file">{file_icon} {display_text}</span></li>'
                    )
        if other_structure:
            for name, content in iter_subdirectories(other_structure):
                if name in structure:
                    continue
                dir_class = ' class="directory-unique-right"'

                folder_icon = get_icon(name, is_dir=True, style=icon_style)

                metrics = format_dir_metrics(
                    content,
                    sort_by_loc=sort_by_loc,
                    sort_by_size=sort_by_size,
                    sort_by_mtime=sort_by_mtime,
                )
                html_content.append(
                    f'<li{dir_class}><span class="directory">{folder_icon} '
                    f"{html.escape(name)}{metrics}</span>"
                )
                if isinstance(content, dict) and content.get("_max_depth_reached"):
                    html_content.append(
                        '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                    )
                else:
                    html_content.append(_build_html_tree({}, content))
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

    _sl = bool(metadata.get("sort_by_loc"))
    _ss = bool(metadata.get("sort_by_size"))
    _sm = bool(metadata.get("sort_by_mtime"))
    dir1_title = dir1_name + format_metrics_suffix(
        dir1_structure.get("_loc", 0),
        dir1_structure.get("_size", 0),
        dir1_structure.get("_mtime", 0.0),
        sort_by_loc=_sl and "_loc" in dir1_structure,
        sort_by_size=_ss and "_size" in dir1_structure,
        sort_by_mtime=_sm and "_mtime" in dir1_structure,
    )
    dir2_title = dir2_name + format_metrics_suffix(
        dir2_structure.get("_loc", 0),
        dir2_structure.get("_size", 0),
        dir2_structure.get("_mtime", 0.0),
        sort_by_loc=_sl and "_loc" in dir2_structure,
        sort_by_size=_ss and "_size" in dir2_structure,
        sort_by_mtime=_sm and "_mtime" in dir2_structure,
    )

    root_icon1 = get_icon(dir1_name, is_dir=True, style=icon_style)
    root_icon2 = get_icon(dir2_name, is_dir=True, style=icon_style)

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
                <h3>{root_icon1} {dir1_title}</h3>
                <p><em>Path: {dir1_path}</em></p>
                {_build_html_tree(dir1_structure, dir2_structure)}
            </div>
            <div class="directory-tree">
                <h3>{root_icon2} {dir2_title}</h3>
                <p><em>Path: {dir2_path}</em></p>
                {_build_html_tree(dir2_structure, dir1_structure)}
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
