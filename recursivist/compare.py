"""Side-by-side directory comparison.

Builds the structures for two directories with identical filtering and renders
them next to each other, highlighting entries unique to either side. Supports
the same filtering and metric options as the single-tree renderer, with
terminal output for interactive use and HTML export for sharing.
"""

import contextlib
import html
import logging
import os
from collections.abc import Mapping, Sequence
from re import Pattern
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from recursivist._models import FileEntry
from recursivist.filtering import compile_regex_patterns
from recursivist.flags import METRIC_GIT, DisplayOptions
from recursivist.git_status import get_git_status
from recursivist.github import (
    GitHubTarget,
    apply_github_urls,
    checkout_repository,
    parse_github_url,
)
from recursivist.icons import get_icon
from recursivist.metrics import (
    format_dir_metrics,
    format_metrics,
    format_metrics_suffix,
)
from recursivist.scanner import get_directory_structure, iter_subdirectories
from recursivist.sorting import sort_files_by_type

logger = logging.getLogger(__name__)


def _scan_one_side(
    scan_dir: str,
    exclude_dirs: Sequence[str] | None,
    ignore_file: str | None,
    exclude_extensions: set[str] | None,
    exclude_patterns: Sequence[str | Pattern[str]] | None,
    include_patterns: Sequence[str | Pattern[str]] | None,
    max_depth: int,
    show_full_path: bool,
    spec: DisplayOptions,
) -> dict[str, Any]:
    """Scan a single already-resolved directory for one side of a comparison.

    Git status is looked up (and files annotated) only when *spec* requests it.
    Callers pass a spec with Git status and modification time already removed
    for GitHub sides (see
    :meth:`~recursivist.flags.DisplayOptions.without_remote_unsupported`), so a
    hosted repository is never given Git markers or per-file timestamps.

    Args:
        scan_dir: The local directory to scan (a real directory, or the
            temporary checkout of a GitHub repository).
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Ignore filename to honor, or ``None``.
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include.
        max_depth: Maximum depth to scan, or ``0`` for unlimited.
        show_full_path: Whether to store absolute paths instead of bare names.
        spec: Resolved sorting and annotation directives for this side.

    Returns:
        The scanned structure for this side.
    """
    need_git = spec.show_git_status or spec.sort_key == METRIC_GIT
    git_status_map: dict[str, str] | None = None
    if need_git:
        git_status_map = get_git_status(scan_dir)
    structure, _ = get_directory_structure(
        scan_dir,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
        max_depth=max_depth,
        show_full_path=show_full_path,
        sort_by_loc=spec.show_loc,
        sort_by_size=spec.show_size,
        sort_by_mtime=spec.show_mtime,
        show_git_status=need_git,
        git_status_map=git_status_map,
    )
    return structure


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
    spec: DisplayOptions | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Scan two inputs for comparison, each a local directory or GitHub URL.

    Each side is scanned with the same filtering and metric settings. A side
    may be a local directory or a GitHub repository URL; a GitHub side is
    downloaded and extracted to a temporary directory (removed before this
    function returns), scanned there, and — when *show_full_path* is set — has
    its file paths rewritten to GitHub blob URLs.

    The ``--ignore-file`` option, Git-status annotations, and modification-time
    annotations only apply to local directories, so they are skipped for any
    GitHub side (its spec is adjusted via
    :meth:`~recursivist.flags.DisplayOptions.without_remote_unsupported`) while
    still being honored for a local side. When *both* sides are GitHub
    repositories the caller is expected to have already cleared these from
    *spec* as well.

    Args:
        dir1: First input — a local directory path or a GitHub repository URL.
        dir2: Second input — a local directory path or a GitHub repository URL.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor for local sides (e.g.
            ``.gitignore``); ignored for GitHub sides.
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include, which
            override the exclusions.
        max_depth: Maximum depth to scan, or ``0`` for unlimited.
        show_full_path: Whether to store absolute paths (local sides) or GitHub
            blob URLs (GitHub sides) instead of bare filenames.
        spec: Resolved sorting and annotation directives. When Git status is
            requested it is looked up independently for each *local* side.
            Defaults to a plain :class:`DisplayOptions`.

    Returns:
        A ``(structure1, structure2)`` tuple holding each input's structure.
    """
    if spec is None:
        spec = DisplayOptions()
    remote_spec = spec.without_remote_unsupported()

    target1 = parse_github_url(dir1)
    target2 = parse_github_url(dir2)

    def _side(
        stack: contextlib.ExitStack,
        raw: str,
        target: GitHubTarget | None,
    ) -> dict[str, Any]:
        if target is None:
            return _scan_one_side(
                raw,
                exclude_dirs,
                ignore_file,
                exclude_extensions,
                exclude_patterns,
                include_patterns,
                max_depth,
                show_full_path,
                spec,
            )
        checkout = stack.enter_context(checkout_repository(target))
        structure = _scan_one_side(
            checkout.local_root,
            exclude_dirs,
            None,
            exclude_extensions,
            exclude_patterns,
            include_patterns,
            max_depth,
            show_full_path,
            remote_spec,
        )
        if show_full_path:
            apply_github_urls(structure, checkout)
        return structure

    with contextlib.ExitStack() as stack:
        structure1 = _side(stack, dir1, target1)
        structure2 = _side(stack, dir2, target2)
        return structure1, structure2


def _comparison_identity(
    entry: FileEntry,
    metrics: Sequence[str],
    show_git_status: bool,
    markers: Mapping[str, str],
) -> tuple[str, str, str]:
    """Return the key that decides whether a file matches one across the sides.

    Comparison highlighting used to key on the filename alone, so two
    identically named files were always treated as the same entry — even when
    an active annotating option gave them different values. This folds the
    *displayed* annotations into the identity so that a file counts as shared
    only when it also presents identically:

    * the numeric metrics named in *metrics* (LOC, size, mtime), rendered in
      the same order they are shown, and
    * the Git-status badge, when *show_git_status* is set.

    Because the identity mirrors the rendered annotation rather than the raw
    values, a difference in the key always corresponds to a visible difference
    in the tree (e.g. ``shared.py (3 lines)`` vs ``shared.py (1 line)``, or a
    ``[M]`` badge on only one side). Only the bare *name* is used for the
    filename component, never the full path, so full-path display does not by
    itself make every file look unique.

    Args:
        entry: The file whose identity is wanted.
        metrics: The numeric metrics being displayed, in display order.
        show_git_status: Whether the Git-status badge is displayed.
        markers: The ``{filename: status_char}`` map for *entry*'s own side.

    Returns:
        A ``(name, metric_annotation, git_badge)`` tuple usable as a set key.
    """
    metric_annotation = format_metrics(entry.loc, entry.size, entry.mtime, metrics)
    git_badge = ""
    if show_git_status:
        marker = markers.get(entry.name, "")
        git_badge = f"[{marker}]" if marker else ""
    return (entry.name, metric_annotation, git_badge)


def build_comparison_tree(
    structure: dict[str, Any],
    other_structure: dict[str, Any],
    tree: Tree,
    spec: DisplayOptions,
    show_full_path: bool = False,
    icon_style: str = "emoji",
    identity_spec: DisplayOptions | None = None,
    *,
    this_is_remote: bool = False,
    other_is_remote: bool = False,
) -> None:
    """Populate a ``rich`` tree, highlighting differences against another tree.

    Recursively adds the entries of *structure* to *tree*, comparing each
    against *other_structure*: items present in both are shown normally, items
    unique to *structure* are highlighted in green, and items unique to
    *other_structure* are highlighted in red. File names are rendered without
    file-type-specific colors so the green/red difference highlighting stands
    out. Files are ordered by ``spec.sort_key`` and metric annotations are
    appended in ``spec.metrics`` order.

    When ``spec.show_git_status`` is set, each file is followed by a plain
    Git-status badge — ``[U]`` untracked, ``[M]`` modified, ``[A]`` added,
    ``[D]`` deleted — read from the ``_git_markers`` stored on *structure* (and
    on *other_structure* for entries unique to it). The badge is not
    color-coded; it trails the metric parenthetical, and deleted files are
    struck through.

    Two identically named files count as the same entry only when their
    *displayed* annotations also match (see :func:`_comparison_identity`), so a
    differing metric or Git status marks them as unique to their side.
    *identity_spec* controls which annotations that match considers: it
    defaults to *spec*, but a caller comparing a local directory against a
    hosted repository passes ``spec.without_remote_unsupported()`` so that
    annotations a remote side cannot provide (modification time, Git status)
    are excluded from the identity — those are still *displayed* per *spec*,
    they just no longer split otherwise-matching files across the two sides.

    Args:
        structure: Structure of the directory being rendered.
        other_structure: Structure of the directory being compared against.
        tree: ``rich`` tree to add nodes to. Modified in place.
        spec: Resolved sorting and annotation directives.
        show_full_path: Whether to display absolute paths instead of bare
            filenames.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        identity_spec: Directives governing which annotations contribute to
            cross-side file identity. Defaults to *spec*.
        this_is_remote: Whether the primary structure originates from a hosted repository.
        other_is_remote: Whether the compared structure originates from a hosted repository.
    """
    id_spec = identity_spec if identity_spec is not None else spec
    need_git = spec.show_git_status or spec.sort_key == METRIC_GIT
    git_markers_dict: dict[str, str] = (
        structure.get("_git_markers", {}) if need_git else {}
    )
    other_git_markers: dict[str, str] = (
        other_structure.get("_git_markers", {}) if need_git and other_structure else {}
    )

    this_metrics = (
        tuple(m for m in spec.metrics if m != "mtime")
        if this_is_remote
        else spec.metrics
    )
    other_metrics = (
        tuple(m for m in spec.metrics if m != "mtime")
        if other_is_remote
        else spec.metrics
    )

    def _add_file_node(
        entry: Any, markers: dict[str, str], highlight: str, metrics: Sequence[str]
    ) -> None:
        """Add a single file entry to *tree* with metrics and Git badge.

        The Git badge (``[U]``/``[M]``/``[A]``/``[D]``) is rendered without any
        color of its own; deleted files are struck through.

        Args:
            entry: The :class:`FileEntry` to render.
            markers: The ``{filename: status_char}`` map for this file's side.
            highlight: The background highlight style (``"on green"``,
                ``"on red"``, or ``""``) marking difference state.
            metrics: Displayed metrics for the file.
        """
        file_icon = get_icon(entry.name, is_dir=False, style=icon_style)
        label = f"{file_icon} {entry.path}" + format_metrics_suffix(
            entry.loc, entry.size, entry.mtime, metrics
        )
        git_marker = markers.get(entry.name, "") if need_git else ""
        if git_marker == "D":
            name_style = f"{highlight} strike".strip()
        else:
            name_style = highlight
        text = Text(label, style=name_style)
        if spec.show_git_status and git_marker:
            text.append(f" [{git_marker}]", style=highlight)
        tree.add(text)

    if "_files" in structure:
        files_in_other = other_structure.get("_files", []) if other_structure else []
        other_identities = {
            _comparison_identity(
                FileEntry.coerce(item),
                id_spec.metrics,
                id_spec.show_git_status,
                other_git_markers,
            )
            for item in files_in_other
        }
        for entry in sort_files_by_type(
            structure["_files"], spec.sort_key, git_markers_dict
        ):
            identity = _comparison_identity(
                entry, id_spec.metrics, id_spec.show_git_status, git_markers_dict
            )
            highlight = "on green" if identity not in other_identities else ""
            _add_file_node(entry, git_markers_dict, highlight, this_metrics)
    for folder, content in iter_subdirectories(structure):
        folder_icon = get_icon(folder, is_dir=True, style=icon_style)

        other_content = other_structure.get(folder, {}) if other_structure else {}
        metrics_suffix = format_dir_metrics(content, this_metrics)
        folder_label = f"{folder_icon} {folder}{metrics_suffix}"
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
                spec,
                show_full_path,
                icon_style=icon_style,
                identity_spec=id_spec,
                this_is_remote=this_is_remote,
                other_is_remote=other_is_remote,
            )
    if other_structure and "_files" in other_structure:
        files_in_this = structure.get("_files", [])
        this_identities = {
            _comparison_identity(
                FileEntry.coerce(item),
                id_spec.metrics,
                id_spec.show_git_status,
                git_markers_dict,
            )
            for item in files_in_this
        }
        for entry in sort_files_by_type(
            other_structure["_files"], spec.sort_key, other_git_markers
        ):
            identity = _comparison_identity(
                entry, id_spec.metrics, id_spec.show_git_status, other_git_markers
            )
            if identity not in this_identities:
                _add_file_node(entry, other_git_markers, "on red", other_metrics)
    if other_structure:
        for folder, other_content in iter_subdirectories(other_structure):
            if folder in structure:
                continue
            folder_icon = get_icon(folder, is_dir=True, style=icon_style)

            metrics_suffix = format_dir_metrics(other_content, other_metrics)
            subtree = tree.add(
                Text(f"{folder_icon} {folder}{metrics_suffix}", style="red")
            )
            if isinstance(other_content, dict) and other_content.get(
                "_max_depth_reached"
            ):
                subtree.add(Text("⋯ (max depth reached)", style="dim"))
            else:
                build_comparison_tree(
                    {},
                    other_content,
                    subtree,
                    spec,
                    show_full_path,
                    icon_style=icon_style,
                    identity_spec=id_spec,
                    this_is_remote=this_is_remote,
                    other_is_remote=other_is_remote,
                )


def _side_display_name(raw: str) -> str:
    """Return the label for one comparison side, local path or GitHub URL.

    For a GitHub URL this is the repository name (or the subpath's last
    segment); for a local path it is the directory's own name.

    Args:
        raw: The raw input for one side of the comparison.

    Returns:
        A short display name for the side.
    """
    target = parse_github_url(raw)
    if target is not None:
        return target.display_name
    return os.path.basename(os.path.abspath(raw))


def _identity_spec_for(dir1: str, dir2: str, spec: DisplayOptions) -> DisplayOptions:
    """Return the spec governing cross-side file identity for two inputs.

    When both inputs are local directories the full *spec* is used, so every
    displayed annotation contributes to whether two identically named files are
    treated as the same entry. When either input is a GitHub repository, the
    annotations a hosted side cannot provide — modification time and Git
    status — are dropped from the identity via
    :meth:`~recursivist.flags.DisplayOptions.without_remote_unsupported`, so
    they no longer split otherwise-matching files across the two sides. Those
    annotations are still *displayed* according to *spec*; only their effect on
    difference highlighting changes.

    Args:
        dir1: First input — a local directory path or a GitHub repository URL.
        dir2: Second input — a local directory path or a GitHub repository URL.
        spec: The resolved display directives for the run.

    Returns:
        *spec* unchanged for a local-vs-local comparison, or its
        remote-adjusted form when either side is a GitHub repository.
    """
    involves_remote = (
        parse_github_url(dir1) is not None or parse_github_url(dir2) is not None
    )
    return spec.without_remote_unsupported() if involves_remote else spec


def _render_side_by_side(console: Console, left: Panel, right: Panel) -> Table:
    """Lay two comparison panels out side by side at a fixed half-width each.

    Each pane is pinned to half the available terminal width, with a
    single-column gap between them, so the two panels always render side by
    side. Because the panes cannot grow to fit their content, the wrapped trees
    inside them break long entries — long names, several annotation flags, or
    ``--full-path`` — across lines via the ``"fold"`` overflow, keeping the two
    panes aligned at any width.

    Args:
        console: Console the grid will be printed to; its width sets the split.
        left: Panel for the first directory.
        right: Panel for the second directory.

    Returns:
        A ``rich`` grid holding the two panels side by side.
    """
    gap = 1
    panel_width = max((console.width - gap) // 2, 1)
    grid = Table.grid(padding=0)
    grid.add_column(width=panel_width, overflow="fold")
    grid.add_column(width=gap)
    grid.add_column(width=panel_width, overflow="fold")
    grid.add_row(left, "", right)
    return grid


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
    spec: DisplayOptions | None = None,
    icon_style: str = "emoji",
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
        spec: Resolved sorting and annotation directives. Defaults to a plain
            :class:`DisplayOptions`.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
    """
    if spec is None:
        spec = DisplayOptions()
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
    structure1, structure2 = compare_directory_structures(
        dir1,
        dir2,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        exclude_patterns=compiled_exclude,
        include_patterns=compiled_include,
        max_depth=max_depth,
        show_full_path=show_full_path,
        spec=spec,
    )
    console = Console()

    identity_spec = _identity_spec_for(dir1, dir2, spec)

    is_remote1 = parse_github_url(dir1) is not None
    is_remote2 = parse_github_url(dir2) is not None

    dir1_metrics = (
        tuple(m for m in spec.metrics if m != "mtime") if is_remote1 else spec.metrics
    )
    dir2_metrics = (
        tuple(m for m in spec.metrics if m != "mtime") if is_remote2 else spec.metrics
    )

    root_base1 = _side_display_name(dir1)
    root_base2 = _side_display_name(dir2)
    root_icon1 = get_icon(root_base1, is_dir=True, style=icon_style)
    root_icon2 = get_icon(root_base2, is_dir=True, style=icon_style)

    tree1 = Tree(
        Text(
            f"{root_icon1} {root_base1}" + format_dir_metrics(structure1, dir1_metrics),
            style="bold",
        )
    )

    tree2 = Tree(
        Text(
            f"{root_icon2} {root_base2}" + format_dir_metrics(structure2, dir2_metrics),
            style="bold",
        )
    )

    build_comparison_tree(
        structure1,
        structure2,
        tree1,
        spec,
        show_full_path=show_full_path,
        icon_style=icon_style,
        identity_spec=identity_spec,
        this_is_remote=is_remote1,
        other_is_remote=is_remote2,
    )
    build_comparison_tree(
        structure2,
        structure1,
        tree2,
        spec,
        show_full_path=show_full_path,
        icon_style=icon_style,
        identity_spec=identity_spec,
        this_is_remote=is_remote2,
        other_is_remote=is_remote1,
    )
    legend_text = Text()
    legend_text.append("Legend: ", style="bold")
    legend_text.append("Green", style="on green")
    legend_text.append(" = In this directory, ")
    legend_text.append("Red", style="on red")
    legend_text.append(" = In the other directory")
    if "loc" in spec.metrics:
        legend_text.append("\n")
        legend_text.append("LOC counts shown in parentheses")
    if "size" in spec.metrics:
        legend_text.append("\n")
        legend_text.append("File sizes shown in parentheses")
    if "mtime" in spec.metrics:
        legend_text.append("\n")
        legend_text.append("Modification times shown in parentheses")
    if spec.show_git_status:
        legend_text.append("\n")
        legend_text.append(
            "Git status markers: [U] untracked, [M] modified, [A] added, [D] deleted"
        )
    _sort_note = {
        "loc": "Files sorted by line count",
        "size": "Files sorted by size",
        "mtime": "Files sorted by modification time (newest first)",
        "git_status": "Files sorted by Git status",
        "similarity": "Files grouped by name similarity",
    }.get(spec.sort_key or "")
    if _sort_note:
        legend_text.append("\n")
        legend_text.append(_sort_note)
    if max_depth > 0:
        level_word = "level" if max_depth == 1 else "levels"
        legend_text.append("\n")
        legend_text.append("⋯ (max depth reached) ", style="dim")
        legend_text.append(f"= Directory tree is limited to {max_depth} {level_word}")
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
        _render_side_by_side(
            console,
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
    spec: DisplayOptions | None = None,
    icon_style: str = "emoji",
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
        spec: Resolved sorting and annotation directives. Defaults to a plain
            :class:`DisplayOptions`.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.

    Raises:
        ValueError: If *format_type* is not ``"html"``.
    """
    if spec is None:
        spec = DisplayOptions()
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
    structure1, structure2 = compare_directory_structures(
        dir1,
        dir2,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        exclude_patterns=compiled_exclude,
        include_patterns=compiled_include,
        max_depth=max_depth,
        show_full_path=show_full_path,
        spec=spec,
    )
    identity_spec = _identity_spec_for(dir1, dir2, spec)

    is_remote1 = parse_github_url(dir1) is not None
    is_remote2 = parse_github_url(dir2) is not None

    comparison_data = {
        "dir1": {
            "path": dir1,
            "name": _side_display_name(dir1),
            "structure": structure1,
            "is_remote": is_remote1,
        },
        "dir2": {
            "path": dir2,
            "name": _side_display_name(dir2),
            "structure": structure2,
            "is_remote": is_remote2,
        },
        "metadata": {
            "exclude_patterns": [str(p) for p in exclude_patterns],
            "include_patterns": [str(p) for p in include_patterns],
            "pattern_type": "regex" if use_regex else "glob",
            "max_depth": max_depth,
            "show_full_path": show_full_path,
            "metrics": list(spec.metrics),
            "sort_key": spec.sort_key,
            "show_loc": spec.show_loc,
            "show_size": spec.show_size,
            "show_mtime": spec.show_mtime,
            "show_git_status": spec.show_git_status,
            "identity_metrics": list(identity_spec.metrics),
            "identity_git": identity_spec.show_git_status,
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
    by side and their differences highlighted, including any LOC, size,
    modification-time, or Git-status annotations enabled in the metadata.

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
        this_is_remote: bool,
        other_is_remote: bool,
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
        _meta = comparison_data.get("metadata", {})
        show_full_path = _meta.get("show_full_path", False)
        metrics = _meta.get("metrics", [])
        sort_key = _meta.get("sort_key")
        show_git_status = _meta.get("show_git_status", False)
        identity_metrics = _meta.get("identity_metrics", metrics)
        identity_git = _meta.get("identity_git", show_git_status)

        this_metrics = (
            [m for m in metrics if m != "mtime"] if this_is_remote else metrics
        )
        other_metrics = (
            [m for m in metrics if m != "mtime"] if other_is_remote else metrics
        )

        git_markers = structure.get("_git_markers", {}) if show_git_status else {}
        other_git_markers = (
            other_structure.get("_git_markers", {})
            if show_git_status and other_structure
            else {}
        )
        _GIT_HTML_MARKERS = {"U", "M", "A", "D"}

        def _file_li(
            entry: Any,
            markers: dict[str, str],
            file_class: str,
            file_metrics: Sequence[str],
        ) -> str:
            """Render one file ``<li>`` with metrics and an optional Git badge.

            The badge is not color-coded; deleted files are struck through.

            Args:
                entry: The :class:`FileEntry` to render.
                markers: The ``{filename: status_char}`` map for this side.
                file_class: The ``class="..."`` attribute (including a leading
                    space) marking difference state, or ``""``.
                file_metrics: Specific metrics for this file.

            Returns:
                The ``<li>`` HTML fragment for the file.
            """
            base = entry.path if show_full_path else entry.name
            escaped = html.escape(base)
            git_marker = markers.get(entry.name, "") if show_git_status else ""
            if git_marker and git_marker in _GIT_HTML_MARKERS:
                git_badge = (
                    f' <span class="git-badge git-{git_marker.lower()}" '
                    f'style="font-size:0.8em;font-weight:bold;">'
                    f"[{git_marker}]</span>"
                )
                if git_marker == "D":
                    escaped = (
                        f'<span style="text-decoration: line-through;">{escaped}</span>'
                    )
            else:
                git_badge = ""
            display_text = escaped + format_metrics_suffix(
                entry.loc, entry.size, entry.mtime, file_metrics
            )
            file_icon = get_icon(entry.name, is_dir=False, style=icon_style)
            return (
                f'<li{file_class}><span class="file">{file_icon} '
                f"{display_text}</span>{git_badge}</li>"
            )

        files_in_this = structure.get("_files", [])
        if "_files" in structure:
            files_in_other = (
                other_structure.get("_files", []) if other_structure else []
            )
            other_identities = {
                _comparison_identity(
                    FileEntry.coerce(item),
                    identity_metrics,
                    identity_git,
                    other_git_markers,
                )
                for item in files_in_other
            }
            sorted_files = sort_files_by_type(files_in_this, sort_key, git_markers)
            for entry in sorted_files:
                identity = _comparison_identity(
                    entry, identity_metrics, identity_git, git_markers
                )
                if identity not in other_identities:
                    file_class = ' class="file-unique-left"'
                else:
                    file_class = ""
                html_content.append(
                    _file_li(entry, git_markers, file_class, this_metrics)
                )
        for name, content in iter_subdirectories(structure):
            if name not in other_structure:
                dir_class = ' class="directory-unique-left"'
            else:
                dir_class = ""

            folder_icon = get_icon(name, is_dir=True, style=icon_style)

            metrics_suffix = format_dir_metrics(content, this_metrics)
            html_content.append(
                f'<li{dir_class}><span class="directory">{folder_icon} '
                f"{html.escape(name)}{metrics_suffix}</span>"
            )
            if isinstance(content, dict) and content.get("_max_depth_reached"):
                html_content.append(
                    '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                )
            else:
                other_content = other_structure.get(name, {}) if other_structure else {}
                html_content.append(
                    _build_html_tree(
                        content, other_content, this_is_remote, other_is_remote
                    )
                )
            html_content.append("</li>")
        if other_structure and "_files" in other_structure:
            this_identities = {
                _comparison_identity(
                    FileEntry.coerce(item), identity_metrics, identity_git, git_markers
                )
                for item in files_in_this
            }
            sorted_other_files = sort_files_by_type(
                other_structure["_files"], sort_key, other_git_markers
            )
            for entry in sorted_other_files:
                identity = _comparison_identity(
                    entry, identity_metrics, identity_git, other_git_markers
                )
                if identity not in this_identities:
                    html_content.append(
                        _file_li(
                            entry,
                            other_git_markers,
                            ' class="file-unique-right"',
                            other_metrics,
                        )
                    )
        if other_structure:
            for name, content in iter_subdirectories(other_structure):
                if name in structure:
                    continue
                dir_class = ' class="directory-unique-right"'

                folder_icon = get_icon(name, is_dir=True, style=icon_style)

                metrics_suffix = format_dir_metrics(content, other_metrics)
                html_content.append(
                    f'<li{dir_class}><span class="directory">{folder_icon} '
                    f"{html.escape(name)}{metrics_suffix}</span>"
                )
                if isinstance(content, dict) and content.get("_max_depth_reached"):
                    html_content.append(
                        '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                    )
                else:
                    html_content.append(
                        _build_html_tree({}, content, this_is_remote, other_is_remote)
                    )
                html_content.append("</li>")
        html_content.append("</ul>")
        return "\n".join(html_content)

    dir1_name = html.escape(comparison_data["dir1"]["name"])
    dir2_name = html.escape(comparison_data["dir2"]["name"])
    dir1_path = html.escape(comparison_data["dir1"]["path"])
    dir2_path = html.escape(comparison_data["dir2"]["path"])
    dir1_structure = comparison_data["dir1"]["structure"]
    dir2_structure = comparison_data["dir2"]["structure"]

    dir1_is_remote = comparison_data["dir1"].get("is_remote", False)
    dir2_is_remote = comparison_data["dir2"].get("is_remote", False)

    metadata = comparison_data.get("metadata", {})
    max_depth_info = ""
    max_depth_val = metadata.get("max_depth", 0)
    if max_depth_val > 0:
        level_word = "level" if max_depth_val == 1 else "levels"
        max_depth_info = f'<div class="info-block"><span class="info-label">Max Depth:</span> {max_depth_val} {level_word}</div>'
    path_info = ""
    if metadata.get("show_full_path"):
        path_info = '<div class="info-block"><span class="info-label">Path Display:</span> Full paths shown</div>'
    loc_info = ""
    if metadata.get("show_loc"):
        loc_info = '<div class="info-block"><span class="info-label">Lines of Code:</span> LOC counts displayed</div>'
    size_info = ""
    if metadata.get("show_size"):
        size_info = '<div class="info-block"><span class="info-label">File Sizes:</span> File sizes displayed</div>'
    mtime_info = ""
    if metadata.get("show_mtime"):
        mtime_info = '<div class="info-block"><span class="info-label">Modification Times:</span> Timestamps displayed</div>'
    git_status_info = ""
    if metadata.get("show_git_status"):
        git_status_info = (
            '<div class="info-block"><span class="info-label">Git Status:</span> '
            "Status markers displayed &mdash; "
            '<span class="git-badge git-u">[U]</span> untracked, '
            '<span class="git-badge git-m">[M]</span> modified, '
            '<span class="git-badge git-a">[A]</span> added, '
            '<span class="git-badge git-d">[D]</span> deleted</div>'
        )
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

    _metrics = metadata.get("metrics", [])
    dir1_metrics = [m for m in _metrics if m != "mtime"] if dir1_is_remote else _metrics
    dir2_metrics = [m for m in _metrics if m != "mtime"] if dir2_is_remote else _metrics

    dir1_title = dir1_name + format_dir_metrics(dir1_structure, dir1_metrics)
    dir2_title = dir2_name + format_dir_metrics(dir2_structure, dir2_metrics)

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
            .git-badge {{
                font-size: 0.8em;
                font-weight: bold;
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
        {git_status_info}
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
                {_build_html_tree(dir1_structure, dir2_structure, dir1_is_remote, dir2_is_remote)}
            </div>
            <div class="directory-tree">
                <h3>{root_icon2} {dir2_title}</h3>
                <p><em>Path: {dir2_path}</em></p>
                {_build_html_tree(dir2_structure, dir1_structure, dir2_is_remote, dir1_is_remote)}
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
