"""Terminal tree rendering.

Builds and prints a ``rich`` tree from a scanned structure, with extension colors,
optional metric annotations, and Git status markers. The structure comes from
[`get_directory_structure`][recursivist.scanner.get_directory_structure], which applies
all filtering.
"""

import os

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from recursivist._models import Directory
from recursivist.colors import build_color_map
from recursivist.flags import METRIC_GIT, DisplayOptions
from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics, format_metrics_suffix
from recursivist.scanner import has_contents, iter_subdirectories
from recursivist.sorting import sort_files_by_type

_GIT_MARKER_STYLES: dict[str, tuple[str, str]] = {
    "U": ("dim", "[U]"),
    "M": ("yellow", "[M]"),
    "A": ("green", "[A]"),
    "D": ("red", "[D]"),
}


def build_tree(
    structure: Directory,
    tree: Tree,
    color_map: dict[str, str],
    spec: DisplayOptions,
    icon_style: str = "emoji",
) -> None:
    """Populate a ``rich`` tree from a scanned directory structure.

    Recursively adds each file and subdirectory of *structure* to *tree*, with filenames
    colored by extension. Each file is labeled with its stored ``path``, which already
    holds the full path when the scan requested one. Files are ordered by
    ``spec.sort_key`` via
    [`recursivist.sorting.sort_files_by_type`][recursivist.sorting.sort_files_by_type].
    A subtree that hit the depth limit is simply left unexpanded; its folder icon still
    shows whether anything was cut off.

    The resolved *spec* controls the annotations appended to each entry:

    - ``spec.metrics``: the ordered lines-of-code, size, and modification-time metrics
      to append (in the exact order requested).
    - ``spec.date_format``: how a modification time is written, ``"relative"`` or
      ``"iso"``.
    - ``spec.show_git_status``: append a colored marker to each file — ``[U]`` untracked
      (grey), ``[M]`` modified (yellow), ``[A]`` added (green), ``[D]`` deleted (red).
      The marker always trails the metric parenthetical, and deleted files no longer on
      disk are also struck through.

    Args:
        structure: Directory to render.
        tree: ``rich`` tree to add nodes to. Modified in place.
        color_map: Mapping of lowercase file extension to hex color.
        spec: Resolved sorting and annotation directives.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
    """
    need_git = spec.show_git_status or spec.sort_key == METRIC_GIT
    git_markers_dict: dict[str, str] = structure.git_markers if need_git else {}
    for entry in sort_files_by_type(structure.files, spec.sort_key, git_markers_dict):
        ext = os.path.splitext(entry.name)[1].lower()
        color = color_map.get(ext, "#FFFFFF")

        git_marker = git_markers_dict.get(entry.name, "")
        is_deleted = git_marker == "D"

        name_style = f"{color} strike" if is_deleted else color

        colored_text = Text()
        icon = get_icon(entry.name, is_dir=False, style=icon_style)
        colored_text.append(f"{icon} ", style=color)
        colored_text.append(
            entry.path
            + format_metrics_suffix(
                entry.loc, entry.size, entry.mtime, spec.metrics, spec.date_format
            ),
            style=name_style,
        )

        if spec.show_git_status and git_marker:
            marker_style, badge = _GIT_MARKER_STYLES.get(
                git_marker, ("dim", f"[{git_marker}]")
            )
            colored_text.append(f" {badge}", style=marker_style)

        tree.add(colored_text)
    for folder, content in iter_subdirectories(structure):
        folder_icon = get_icon(
            folder,
            is_dir=True,
            style=icon_style,
            is_empty=not has_contents(content),
        )
        metrics = format_dir_metrics(content, spec.metrics, spec.date_format)
        folder_display = f"{folder_icon} {folder}{metrics}"
        subtree = tree.add(Text(folder_display))
        if content.symlink_loop:
            subtree.add(Text("↩ (symlink loop)", style="dim"))
        elif not content.max_depth_reached:
            build_tree(content, subtree, color_map, spec, icon_style)


def display_tree(
    structure: Directory,
    extensions: set[str],
    root_name: str,
    spec: DisplayOptions | None = None,
    icon_style: str = "emoji",
) -> None:
    """Render a scanned directory structure as a tree in the terminal.

    Builds a color map from *extensions*, populates a ``rich`` tree from *structure*
    with [`build_tree`][recursivist.tree.build_tree], and prints it. *structure* is
    rendered exactly as given: exclusions, depth limits, full paths, metrics, and Git
    status are all determined by the scan that produced it.

    Args:
        structure: Scanned directory structure to render, as returned by
            [`get_directory_structure`][recursivist.scanner.get_directory_structure].
        extensions: Set of file extensions found in *structure*, as returned alongside
            it by the scan.
        root_name: Display name for the root node (e.g. the directory's basename, or a
            repository name for a GitHub input).
        spec: Resolved sorting and annotation directives. Defaults to a plain
            [`DisplayOptions`][recursivist.flags.DisplayOptions] (no sorting, no
            annotations). Metrics and Git status are only shown if the scan collected
            them.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
    """
    if spec is None:
        spec = DisplayOptions()

    color_map = build_color_map(extensions)
    root_icon = get_icon(
        root_name,
        is_dir=True,
        style=icon_style,
        is_empty=not has_contents(structure),
    )
    root_label = f"{root_icon} {root_name}" + format_dir_metrics(
        structure, spec.metrics, spec.date_format
    )
    tree = Tree(Text(root_label))
    build_tree(structure, tree, color_map, spec, icon_style=icon_style)
    Console().print(tree)
