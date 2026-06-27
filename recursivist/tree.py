"""Terminal tree rendering.

Builds and prints a ``rich`` tree from a scanned structure, with extension
colors, optional metric annotations, and Git status markers. This is the top
of the dependency stack, composing the scanner, filtering, colors, metrics,
sorting, and icon modules.
"""

import logging
import os
from typing import Any

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from recursivist.colors import generate_color_for_extension
from recursivist.filtering import compile_regex_patterns
from recursivist.git_status import get_git_status
from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics, format_metrics_suffix
from recursivist.scanner import get_directory_structure, iter_subdirectories
from recursivist.sorting import sort_files_by_type

logger = logging.getLogger(__name__)


def build_tree(
    structure: dict[str, Any],
    tree: Tree,
    color_map: dict[str, str],
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
    show_git_status: bool = False,
    icon_style: str = "emoji",
    sort_by_similarity: bool = False,
) -> None:
    """Populate a ``rich`` tree from a scanned directory structure.

    Recursively adds each file and subdirectory of *structure* to *tree*, with
    filenames colored by extension. Files are ordered by
    :func:`recursivist.sorting.sort_files_by_type`, and a subtree that hit the
    depth limit is shown as a single "max depth reached" placeholder.

    The active sort/display flags control the annotations appended to each
    entry:

    - *sort_by_loc*, *sort_by_size*, *sort_by_mtime*: append the corresponding
      lines-of-code, size, and modification-time metrics.
    - *sort_by_similarity*: group files with similar names together. Applies
      only when no numeric sort is active and adds no annotation of its own.
    - *show_git_status*: append a colored marker to each file — ``[U]``
      untracked (grey), ``[M]`` modified (yellow), ``[A]`` added (green),
      ``[D]`` deleted (red). Deleted files no longer on disk are also struck
      through.

    Args:
        structure: Directory-structure dict to render.
        tree: ``rich`` tree to add nodes to. Modified in place.
        color_map: Mapping of lowercase file extension to hex color.
        show_full_path: Whether to display absolute paths instead of bare
            filenames.
        sort_by_loc: Whether to display lines-of-code counts.
        sort_by_size: Whether to display file sizes.
        sort_by_mtime: Whether to display modification times.
        show_git_status: Whether to display Git status markers.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        sort_by_similarity: Whether to group files by name similarity.
    """
    _GIT_MARKER_STYLES = {
        "U": ("dim", "[U]"),
        "M": ("yellow", "[M]"),
        "A": ("green", "[A]"),
        "D": ("red", "[D]"),
    }
    git_markers_dict: dict[str, str] = (
        structure.get("_git_markers", {}) if show_git_status else {}
    )
    if "_files" in structure:
        for entry in sort_files_by_type(
            structure["_files"],
            sort_by_loc,
            sort_by_size,
            sort_by_mtime,
            sort_by_similarity,
        ):
            display_path = entry.path if show_full_path else entry.name
            ext = os.path.splitext(entry.name)[1].lower()
            color = color_map.get(ext, "#FFFFFF")

            git_marker = git_markers_dict.get(entry.name, "")
            is_deleted = git_marker == "D"

            name_style = f"{color} strike" if is_deleted else color

            colored_text = Text()
            icon = get_icon(entry.name, is_dir=False, style=icon_style)
            colored_text.append(f"{icon} ", style=color)
            colored_text.append(
                display_path
                + format_metrics_suffix(
                    entry.loc,
                    entry.size,
                    entry.mtime,
                    sort_by_loc=sort_by_loc,
                    sort_by_size=sort_by_size,
                    sort_by_mtime=sort_by_mtime,
                ),
                style=name_style,
            )

            if show_git_status and git_marker:
                marker_style, badge = _GIT_MARKER_STYLES.get(
                    git_marker, ("dim", f"[{git_marker}]")
                )
                colored_text.append(f" {badge}", style=marker_style)

            tree.add(colored_text)
    for folder, content in iter_subdirectories(structure):
        folder_icon = get_icon(folder, is_dir=True, style=icon_style)
        metrics = format_dir_metrics(
            content,
            sort_by_loc=sort_by_loc,
            sort_by_size=sort_by_size,
            sort_by_mtime=sort_by_mtime,
        )
        folder_display = f"{folder_icon} {folder}{metrics}"
        subtree = tree.add(folder_display)
        if isinstance(content, dict) and content.get("_max_depth_reached"):
            subtree.add(Text("⋯ (max depth reached)", style="dim"))
        else:
            build_tree(
                content,
                subtree,
                color_map,
                show_full_path,
                sort_by_loc,
                sort_by_size,
                sort_by_mtime,
                show_git_status,
                icon_style,
                sort_by_similarity,
            )


def display_tree(
    root_dir: str,
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
    show_git_status: bool = False,
    icon_style: str = "emoji",
    structure: dict[str, Any] | None = None,
    extensions: set[str] | None = None,
    sort_by_similarity: bool = False,
) -> None:
    """Scan a directory and render it as a tree in the terminal.

    Runs the full pipeline — optionally fetching Git status, scanning the
    directory, building a color map, and printing a ``rich`` tree — unless a
    pre-computed *structure* and *extensions* are supplied, in which case the
    scan is skipped and those are rendered directly.

    Args:
        root_dir: Directory to display.
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
        show_git_status: Whether to annotate files with Git status markers.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        structure: Pre-computed directory structure. When given together with
            *extensions*, the directory is not re-scanned.
        extensions: Pre-computed set of file extensions matching *structure*.
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

    if structure is None or extensions is None:
        exclude_extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in exclude_extensions
        }
        compiled_exclude = compile_regex_patterns(exclude_patterns, use_regex)
        compiled_include = compile_regex_patterns(include_patterns, use_regex)

        git_status_map: dict[str, str] | None = None
        if show_git_status:
            git_status_map = get_git_status(root_dir)
            if not git_status_map:
                logger.debug(
                    "Git status requested but no data returned — "
                    "directory may not be inside a Git repository, or there are no changes."
                )

        structure, extensions = get_directory_structure(
            root_dir=root_dir,
            exclude_dirs=exclude_dirs,
            ignore_file=ignore_file,
            exclude_extensions=exclude_extensions,
            parent_ignore_patterns=None,
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
    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}
    console = Console()

    root_base = os.path.basename(root_dir)
    root_icon = get_icon(root_base, is_dir=True, style=icon_style)
    root_label = f"{root_icon} {root_base}" + format_metrics_suffix(
        structure.get("_loc", 0),
        structure.get("_size", 0),
        structure.get("_mtime", 0.0),
        sort_by_loc=sort_by_loc and "_loc" in structure,
        sort_by_size=sort_by_size and "_size" in structure,
        sort_by_mtime=sort_by_mtime and "_mtime" in structure,
    )
    tree = Tree(root_label)
    build_tree(
        structure,
        tree,
        color_map,
        show_full_path=show_full_path,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
        show_git_status=show_git_status,
        icon_style=icon_style,
        sort_by_similarity=sort_by_similarity,
    )
    console.print(tree)
