"""Side-by-side directory comparison.

Builds the structures for two directories with identical filtering and renders them next
to each other, highlighting entries unique to either side. Supports the same filtering
and metric options as the single-tree renderer, with terminal output for interactive use
and HTML export for sharing.
"""

import contextlib
import html
import logging
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from re import Pattern
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from recursivist._models import FileEntry
from recursivist.filtering import PatternMatchTracker, compile_regex_patterns
from recursivist.flags import METRIC_GIT, METRIC_MTIME, DisplayOptions
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
from recursivist.scanner import (
    get_directory_structure,
    get_subdirectory,
    has_contents,
    iter_subdirectories,
)
from recursivist.sorting import sort_files_by_type

logger = logging.getLogger(__name__)

_Targets = tuple[GitHubTarget | None, GitHubTarget | None]
"""Both comparison inputs as parsed by
[`parse_github_url`][recursivist.github.parse_github_url], in ``(dir1, dir2)`` order;
each item is ``None`` for a local directory."""


def _resolve_targets(dir1: str, dir2: str, targets: _Targets | None) -> _Targets:
    """Return the parsed GitHub targets for both inputs, parsing only if needed.

    Every stage of a comparison needs to know which inputs are GitHub repositories. The
    inputs are parsed once, by whichever entry point is called first, and the result is
    handed down from there rather than being re-derived at each stage.

    Args:
        dir1: First input — a local directory path or a GitHub repository URL.
        dir2: Second input — a local directory path or a GitHub repository URL.
        targets: The already-parsed targets, or ``None`` to parse the inputs now.

    Returns:
        *targets* unchanged when given, otherwise the freshly parsed pair.
    """
    if targets is not None:
        return targets
    return parse_github_url(dir1), parse_github_url(dir2)


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
    pattern_tracker: PatternMatchTracker | None = None,
) -> dict[str, Any]:
    """Scan a single already-resolved directory for one side of a comparison.

    Git status is looked up (and files annotated) only when *spec* requests it. Callers
    pass a spec with Git status and modification time already removed for GitHub sides
    (see
    [`without_remote_unsupported`][recursivist.flags.DisplayOptions.without_remote_unsupported]),
    so a hosted repository is never given Git markers or per-file timestamps.

    Args:
        scan_dir: The local directory to scan (a real directory, or the temporary
            checkout of a GitHub repository).
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Ignore filename to honor, or ``None``.
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include.
        max_depth: Maximum depth to scan, or ``0`` for unlimited.
        show_full_path: Whether to store absolute paths instead of bare names.
        spec: Resolved sorting and annotation directives for this side.
        pattern_tracker: Shared record of which filters matched, so a comparison can
            report filters that matched nothing on either side.

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
        pattern_tracker=pattern_tracker,
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
    *,
    targets: _Targets | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Scan two inputs for comparison, each a local directory or GitHub URL.

    Each side is scanned with the same filtering and metric settings. A side may be a
    local directory or a GitHub repository URL; a GitHub side is downloaded and
    extracted to a temporary directory (removed before this function returns), scanned
    there, and — when *show_full_path* is set — has its file paths rewritten to GitHub
    blob URLs.

    The ``--ignore-file`` option, Git-status annotations, and modification-time
    annotations only apply to local directories, so they are skipped for any GitHub side
    (its spec is adjusted via
    [`without_remote_unsupported`][recursivist.flags.DisplayOptions.without_remote_unsupported])
    while still being honored for a local side. When *both* sides are GitHub
    repositories the caller is expected to have already cleared these from *spec* as
    well.

    Args:
        dir1: First input — a local directory path or a GitHub repository URL.
        dir2: Second input — a local directory path or a GitHub repository URL.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor for local sides (e.g.
            ``.gitignore``); ignored for GitHub sides.
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include. When given, only
            files whose names match one are kept, and a match overrides ignore-file
            rules for that file. They do not override *exclude_dirs*,
            *exclude_extensions*, or *exclude_patterns*.
        max_depth: Maximum depth to scan, or ``0`` for unlimited.
        show_full_path: Whether to store absolute paths (local sides) or GitHub
            blob URLs (GitHub sides) instead of bare filenames.
        spec: Resolved sorting and annotation directives. When Git status is requested
            it is looked up independently for each *local* side. Defaults to a plain
            [`DisplayOptions`][recursivist.flags.DisplayOptions].
        targets: The ``(target1, target2)`` pair already parsed from *dir1* and *dir2*
            with [`parse_github_url`][recursivist.github.parse_github_url] (``None`` for
            a local side), for callers that have it. Left as ``None``, the inputs are
            parsed here.

    Returns:
        A ``(structure1, structure2)`` tuple holding each input's structure.

    Any exclude/include filter that matched no entry on *either* side is logged as a
    warning once both scans finish.
    """
    if spec is None:
        spec = DisplayOptions()
    remote_spec = spec.without_remote_unsupported()

    target1, target2 = _resolve_targets(dir1, dir2, targets)
    tracker = PatternMatchTracker(
        exclude_dirs, exclude_extensions, exclude_patterns, include_patterns
    )

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
                tracker,
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
            tracker,
        )
        if show_full_path:
            apply_github_urls(structure, checkout)
        return structure

    with contextlib.ExitStack() as stack:
        structure1 = _side(stack, dir1, target1)
        structure2 = _side(stack, dir2, target2)
    tracker.report("in either directory")
    return structure1, structure2


_GIT_BADGE_MARKERS = frozenset({"U", "M", "A", "D"})
"""Git status characters that render as a badge on a compared file."""

_SHARED = "shared"
_UNIQUE_THIS = "this"
_UNIQUE_OTHER = "other"


def _side_metrics(metrics: Sequence[str], is_remote: bool) -> tuple[str, ...]:
    """Return the metrics displayable for one side of a comparison.

    A hosted repository has no meaningful modification times, so ``mtime`` is dropped
    for a remote side; a local side displays every requested metric.

    Args:
        metrics: The requested numeric metrics, in display order.
        is_remote: Whether the side originates from a hosted repository.

    Returns:
        The metrics to display for that side, in display order.
    """
    if is_remote:
        return tuple(m for m in metrics if m != METRIC_MTIME)
    return tuple(metrics)


def _git_badge_marker(markers: Mapping[str, str], name: str) -> str:
    """Return the badge-worthy Git status for *name*, or ``""``.

    Both renderers and the cross-side identity go through this one filter, so a marker
    never affects highlighting unless it would also be shown as a badge.

    Args:
        markers: The ``{filename: status_char}`` map for the file's side.
        name: The bare filename.

    Returns:
        The status character if it is one of `_GIT_BADGE_MARKERS`, otherwise ``""``.
    """
    marker = markers.get(name, "")
    return marker if marker in _GIT_BADGE_MARKERS else ""


def _comparison_identity(
    entry: FileEntry,
    metrics: Sequence[str],
    show_git_status: bool,
    markers: Mapping[str, str],
) -> tuple[str, str, str]:
    """Return the key that decides whether a file matches one across the sides.

    Comparison highlighting used to key on the filename alone, so two identically named
    files were always treated as the same entry — even when an active annotating option
    gave them different values. This folds the *displayed* annotations into the identity
    so that a file counts as shared only when it also presents identically:

    * the numeric metrics named in *metrics* (LOC, size, mtime), rendered in the same
      order they are shown, and
    * the Git-status badge, when *show_git_status* is set.

    Because the identity mirrors the rendered annotation rather than the raw values, a
    difference in the key always corresponds to a visible difference in the tree (e.g.
    ``shared.py (3 lines)`` vs ``shared.py (1 line)``, or a ``[M]`` badge on only one
    side). Only the bare *name* is used for the filename component, never the full path,
    so full-path display does not by itself make every file look unique.

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
        marker = _git_badge_marker(markers, entry.name)
        git_badge = f"[{marker}]" if marker else ""
    return (entry.name, metric_annotation, git_badge)


@dataclass(frozen=True)
class _FileNode:
    """A file in the renderer-neutral comparison tree.

    Attributes:
        icon: The file's icon.
        label: The display string (bare name, or full path / URL).
        metrics_suffix: The formatted metric parenthetical, or ``""``.
        git_marker: The Git badge character to show, or ``""`` when none is shown.
        uniqueness: `_SHARED`, `_UNIQUE_THIS` or `_UNIQUE_OTHER`.
    """

    icon: str
    label: str
    metrics_suffix: str
    git_marker: str
    uniqueness: str

    @property
    def deleted(self) -> bool:
        """Whether the file is shown as deleted (and so struck through)."""
        return self.git_marker == "D"


@dataclass(frozen=True)
class _DirNode:
    """A directory in the renderer-neutral comparison tree.

    Attributes:
        icon: The directory's icon.
        name: The directory name.
        metrics_suffix: The formatted aggregate-metric parenthetical, or ``""``.
        uniqueness: `_SHARED`, `_UNIQUE_THIS` or `_UNIQUE_OTHER`.
        symlink_loop: Whether the directory is a symlink back to an ancestor.
        children: The directory's entries, or ``None`` when the depth limit stopped the
            scan before its contents were read.
    """

    icon: str
    name: str
    metrics_suffix: str
    uniqueness: str
    symlink_loop: bool = False
    children: tuple["_FileNode | _DirNode", ...] | None = ()


_Node = _FileNode | _DirNode


@dataclass(frozen=True)
class _ComparisonWalker:
    """Builds the renderer-neutral comparison tree for one side.

    This is the single traversal behind both the terminal and HTML comparison views: it
    decides ordering, which annotations and badges appear, and which entries are unique
    to either side. The renderers only translate the resulting nodes into their output
    format.

    Attributes:
        spec: Resolved sorting and annotation directives.
        identity_spec: Directives governing which annotations contribute to cross-side
            file identity (see `_comparison_identity`).
        this_metrics: Metrics displayed for entries of the side being rendered.
        other_metrics: Metrics displayed for entries unique to the other side.
        icon_style: Icon style, either ``"emoji"`` or ``"nerd"``.
    """

    spec: DisplayOptions
    identity_spec: DisplayOptions
    this_metrics: tuple[str, ...]
    other_metrics: tuple[str, ...]
    icon_style: str = "emoji"

    @classmethod
    def for_sides(
        cls,
        spec: DisplayOptions,
        identity_spec: DisplayOptions | None,
        this_is_remote: bool,
        other_is_remote: bool,
        icon_style: str,
    ) -> "_ComparisonWalker":
        """Create a walker for one side given where each side comes from."""
        return cls(
            spec=spec,
            identity_spec=identity_spec if identity_spec is not None else spec,
            this_metrics=_side_metrics(spec.metrics, this_is_remote),
            other_metrics=_side_metrics(spec.metrics, other_is_remote),
            icon_style=icon_style,
        )

    @property
    def _loads_git_markers(self) -> bool:
        """Whether Git markers are needed, for display *or* for sorting."""
        return self.spec.show_git_status or self.spec.sort_key == METRIC_GIT

    def _identities(
        self, files: Sequence[FileEntry], markers: Mapping[str, str]
    ) -> set[tuple[str, str, str]]:
        return {self._identity(entry, markers) for entry in files}

    def _identity(
        self, entry: FileEntry, markers: Mapping[str, str]
    ) -> tuple[str, str, str]:
        return _comparison_identity(
            entry,
            self.identity_spec.metrics,
            self.identity_spec.show_git_status,
            markers,
        )

    def _file(
        self,
        entry: FileEntry,
        markers: Mapping[str, str],
        uniqueness: str,
        metrics: Sequence[str],
    ) -> _FileNode:
        git_marker = (
            _git_badge_marker(markers, entry.name) if self.spec.show_git_status else ""
        )
        return _FileNode(
            icon=get_icon(entry.name, is_dir=False, style=self.icon_style),
            label=entry.path,
            metrics_suffix=format_metrics_suffix(
                entry.loc, entry.size, entry.mtime, metrics
            ),
            git_marker=git_marker,
            uniqueness=uniqueness,
        )

    def _dir(
        self,
        name: str,
        content: Any,
        this_content: dict[str, Any],
        other_content: dict[str, Any],
        uniqueness: str,
        metrics: Sequence[str],
        is_empty: bool,
    ) -> _DirNode:
        is_dict = isinstance(content, dict)
        symlink_loop = bool(is_dict and content.get("_symlink_loop"))
        children: tuple[_Node, ...] | None
        if symlink_loop:
            children = ()
        elif is_dict and content.get("_max_depth_reached"):
            children = None
        else:
            children = tuple(self.walk(this_content, other_content))
        return _DirNode(
            icon=get_icon(name, is_dir=True, style=self.icon_style, is_empty=is_empty),
            name=name,
            metrics_suffix=format_dir_metrics(content, metrics),
            uniqueness=uniqueness,
            symlink_loop=symlink_loop,
            children=children,
        )

    def walk(
        self, structure: dict[str, Any], other_structure: dict[str, Any]
    ) -> list[_Node]:
        """Return the nodes for *structure*, compared against *other_structure*.

        Entries are ordered: this side's files (sorted), this side's directories, then
        files and directories that exist only on the other side.

        Args:
            structure: Structure of the directory being rendered.
            other_structure: Structure of the directory being compared against.

        Returns:
            The comparison nodes at this level, each directory carrying its children.
        """
        loads_git = self._loads_git_markers
        sort_key = self.spec.sort_key
        markers: dict[str, str] = structure.get("_git_markers", {}) if loads_git else {}
        other_markers: dict[str, str] = (
            other_structure.get("_git_markers", {})
            if loads_git and other_structure
            else {}
        )
        nodes: list[_Node] = []

        if "_files" in structure:
            files_in_other = (
                other_structure.get("_files", []) if other_structure else []
            )
            other_ids = self._identities(files_in_other, other_markers)
            for entry in sort_files_by_type(structure["_files"], sort_key, markers):
                unique = self._identity(entry, markers) not in other_ids
                nodes.append(
                    self._file(
                        entry,
                        markers,
                        _UNIQUE_THIS if unique else _SHARED,
                        self.this_metrics,
                    )
                )

        for name, content in iter_subdirectories(structure):
            other_match = (
                get_subdirectory(other_structure, name) if other_structure else None
            )
            other_content = other_match if other_match is not None else {}
            nodes.append(
                self._dir(
                    name,
                    content,
                    content,
                    other_content,
                    _UNIQUE_THIS if other_match is None else _SHARED,
                    self.this_metrics,
                    is_empty=not (has_contents(content) or has_contents(other_content)),
                )
            )

        if not other_structure:
            return nodes

        if "_files" in other_structure:
            this_ids = self._identities(structure.get("_files", []), markers)
            for entry in sort_files_by_type(
                other_structure["_files"], sort_key, other_markers
            ):
                if self._identity(entry, other_markers) not in this_ids:
                    nodes.append(
                        self._file(
                            entry, other_markers, _UNIQUE_OTHER, self.other_metrics
                        )
                    )

        for name, other_content in iter_subdirectories(other_structure):
            if get_subdirectory(structure, name) is not None:
                continue
            nodes.append(
                self._dir(
                    name,
                    other_content,
                    {},
                    other_content,
                    _UNIQUE_OTHER,
                    self.other_metrics,
                    is_empty=not has_contents(other_content),
                )
            )
        return nodes


_RICH_FILE_HIGHLIGHT = {_UNIQUE_THIS: "on green", _UNIQUE_OTHER: "on red"}
_RICH_DIR_STYLE = {_UNIQUE_THIS: "green", _UNIQUE_OTHER: "red"}


def _render_rich_nodes(nodes: Sequence[_Node], tree: Tree) -> None:
    """Add comparison *nodes* to a ``rich`` tree.

    Unique files get a green/red background and unique directories green/red text.
    Deleted files are struck through; the Git badge trails the metrics, uncolored.

    Args:
        nodes: Nodes produced by `_ComparisonWalker.walk`.
        tree: ``rich`` tree to add nodes to. Modified in place.
    """
    for node in nodes:
        if isinstance(node, _FileNode):
            highlight = _RICH_FILE_HIGHLIGHT.get(node.uniqueness, "")
            style = f"{highlight} strike".strip() if node.deleted else highlight
            text = Text(f"{node.icon} {node.label}{node.metrics_suffix}", style=style)
            if node.git_marker:
                text.append(f" [{node.git_marker}]", style=highlight)
            tree.add(text)
            continue
        subtree = tree.add(
            Text(
                f"{node.icon} {node.name}{node.metrics_suffix}",
                style=_RICH_DIR_STYLE.get(node.uniqueness, ""),
            )
        )
        if node.symlink_loop:
            subtree.add(Text("↩ (symlink loop)", style="dim"))
        elif node.children is not None:
            _render_rich_nodes(node.children, subtree)


_HTML_FILE_CLASS = {
    _UNIQUE_THIS: ' class="file-unique-left"',
    _UNIQUE_OTHER: ' class="file-unique-right"',
}
_HTML_STRIKE = '<span style="text-decoration: line-through;">{}</span>'
_HTML_DIR_CLASS = {
    _UNIQUE_THIS: ' class="directory-unique-left"',
    _UNIQUE_OTHER: ' class="directory-unique-right"',
}


def _render_html_nodes(nodes: Sequence[_Node]) -> str:
    """Render comparison *nodes* as a nested ``<ul>`` fragment.

    Uniqueness becomes a ``*-unique-left``/``*-unique-right`` class. Deleted files are
    struck through; the Git badge trails the metrics, uncolored.

    Args:
        nodes: Nodes produced by `_ComparisonWalker.walk`.

    Returns:
        An HTML fragment representing the directory tree.
    """
    parts = ["<ul>"]
    for node in nodes:
        if isinstance(node, _FileNode):
            display_text = html.escape(node.label + node.metrics_suffix)
            if node.deleted:
                display_text = _HTML_STRIKE.format(display_text)
            git_badge = (
                f' <span class="git-badge">[{node.git_marker}]</span>'
                if node.git_marker
                else ""
            )
            parts.append(
                f"<li{_HTML_FILE_CLASS.get(node.uniqueness, '')}>"
                f'<span class="file">{node.icon} {display_text}</span>{git_badge}</li>'
            )
            continue
        parts.append(
            f"<li{_HTML_DIR_CLASS.get(node.uniqueness, '')}>"
            f'<span class="directory">{node.icon} '
            f"{html.escape(node.name + node.metrics_suffix)}</span>"
        )
        if node.symlink_loop:
            parts.append('<ul><li class="symlink-loop">↩ (symlink loop)</li></ul>')
        elif node.children is not None:
            parts.append(_render_html_nodes(node.children))
        parts.append("</li>")
    parts.append("</ul>")
    return "\n".join(parts)


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

    Recursively adds the entries of *structure* to *tree*, comparing each against
    *other_structure*: items present in both are shown normally, items unique to
    *structure* are highlighted in green, and items unique to *other_structure* are
    highlighted in red. File names are rendered without file-type-specific colors so the
    green/red difference highlighting stands out. Files are ordered by ``spec.sort_key``
    and metric annotations are appended in ``spec.metrics`` order.

    When ``spec.show_git_status`` is set, each file is followed by a plain Git-status
    badge — ``[U]`` untracked, ``[M]`` modified, ``[A]`` added, ``[D]`` deleted — read
    from the ``_git_markers`` stored on *structure* (and on *other_structure* for
    entries unique to it). The badge is not color-coded; it trails the metric
    parenthetical, and deleted files are struck through.

    Two identically named files count as the same entry only when their *displayed*
    annotations also match (see `_comparison_identity`), so a differing metric or Git
    status marks them as unique to their side. *identity_spec* controls which
    annotations that match considers: it defaults to *spec*, but a caller comparing a
    local directory against a hosted repository passes
    ``spec.without_remote_unsupported()`` so that annotations a remote side cannot
    provide (modification time, Git status) are excluded from the identity — those are
    still *displayed* per *spec*, they just no longer split otherwise-matching files
    across the two sides.

    The traversal is shared with the HTML export (see `_ComparisonWalker`), so both
    views always agree on ordering, badges and highlighting.

    Args:
        structure: Structure of the directory being rendered.
        other_structure: Structure of the directory being compared against.
        tree: ``rich`` tree to add nodes to. Modified in place.
        spec: Resolved sorting and annotation directives.
        show_full_path: Accepted for API compatibility. Each file's stored ``path``
            already holds the full path when full-path display was requested.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        identity_spec: Directives governing which annotations contribute to cross-side
            file identity. Defaults to *spec*.
        this_is_remote: Whether the primary structure originates from a hosted
            repository.
        other_is_remote: Whether the compared structure originates from a hosted
            repository.
    """
    del show_full_path
    walker = _ComparisonWalker.for_sides(
        spec, identity_spec, this_is_remote, other_is_remote, icon_style
    )
    _render_rich_nodes(walker.walk(structure, other_structure), tree)


def _side_display_name(raw: str, target: GitHubTarget | None) -> str:
    """Return the label for one comparison side, local path or GitHub URL.

    For a GitHub URL this is the repository name (or the subpath's last segment); for a
    local path it is the directory's own name.

    Args:
        raw: The raw input for one side of the comparison.
        target: The GitHub target parsed from *raw*, or ``None`` for a local path.

    Returns:
        A short display name for the side.
    """
    if target is not None:
        return target.display_name
    return os.path.basename(os.path.abspath(raw))


def _identity_spec_for(
    target1: GitHubTarget | None, target2: GitHubTarget | None, spec: DisplayOptions
) -> DisplayOptions:
    """Return the spec governing cross-side file identity for two inputs.

    When both inputs are local directories the full *spec* is used, so every displayed
    annotation contributes to whether two identically named files are treated as the
    same entry. When either input is a GitHub repository, the annotations a hosted side
    cannot provide — modification time and Git status — are dropped from the identity
    via
    [`without_remote_unsupported`][recursivist.flags.DisplayOptions.without_remote_unsupported],
    so they no longer split otherwise-matching files across the two sides. Those
    annotations are still *displayed* according to *spec*; only their effect on
    difference highlighting changes.

    Args:
        target1: The GitHub target parsed from the first input, or ``None`` if it is a
            local directory.
        target2: The GitHub target parsed from the second input, or ``None`` if it is a
            local directory.
        spec: The resolved display directives for the run.

    Returns:
        *spec* unchanged for a local-vs-local comparison, or its remote-adjusted form
        when either side is a GitHub repository.
    """
    involves_remote = target1 is not None or target2 is not None
    return spec.without_remote_unsupported() if involves_remote else spec


def _render_side_by_side(console: Console, left: Panel, right: Panel) -> Table:
    """Lay two comparison panels out side by side at a fixed half-width each.

    Each pane is pinned to half the available terminal width, with a single-column gap
    between them, so the two panels always render side by side. Because the panes cannot
    grow to fit their content, the wrapped trees inside them break long entries — long
    names, several annotation flags, or ``--full-path`` — across lines via the
    ``"fold"`` overflow, keeping the two panes aligned at any width.

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
    *,
    targets: _Targets | None = None,
) -> None:
    """Render two directory trees side by side in the terminal.

    Scans both directories with identical options and prints them as two labeled,
    color-highlighted panels: entries unique to *dir1* and *dir2* are highlighted in
    contrasting colors, shared entries are shown normally, and a legend explains the
    scheme.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor (e.g. ``.gitignore``).
        exclude_extensions: File extensions to exclude. Normalized to a lowercase,
            dot-prefixed form before scanning.
        exclude_patterns: Glob or regex patterns to exclude.
        include_patterns: Glob or regex patterns to include. When given, only files
            whose names match one are kept, and a match overrides ignore-file rules for
            that file. They do not override *exclude_dirs*, *exclude_extensions*, or
            *exclude_patterns*.
        use_regex: Whether to treat the patterns as regular expressions instead of glob
            patterns.
        max_depth: Maximum depth to display, or ``0`` for unlimited.
        show_full_path: Whether to display absolute paths instead of bare filenames.
        spec: Resolved sorting and annotation directives. Defaults to a plain
            [`DisplayOptions`][recursivist.flags.DisplayOptions].
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        targets: The ``(target1, target2)`` pair already parsed from *dir1* and *dir2*
            with [`parse_github_url`][recursivist.github.parse_github_url] (``None`` for
            a local side), for callers that have it. Left as ``None``, the inputs are
            parsed here.
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
    targets = _resolve_targets(dir1, dir2, targets)
    target1, target2 = targets
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
        targets=targets,
    )
    console = Console()

    identity_spec = _identity_spec_for(target1, target2, spec)

    is_remote1 = target1 is not None
    is_remote2 = target2 is not None

    dir1_metrics = _side_metrics(spec.metrics, is_remote1)
    dir2_metrics = _side_metrics(spec.metrics, is_remote2)

    root_base1 = _side_display_name(dir1, target1)
    root_base2 = _side_display_name(dir2, target2)
    root_icon1 = get_icon(
        root_base1,
        is_dir=True,
        style=icon_style,
        is_empty=not has_contents(structure1),
    )
    root_icon2 = get_icon(
        root_base2,
        is_dir=True,
        style=icon_style,
        is_empty=not has_contents(structure2),
    )

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
        legend_text.append(f"Directory tree is limited to {max_depth} {level_word}")
    if show_full_path:
        legend_text.append("\n")
        legend_text.append("Full file paths are shown instead of just filenames")
    if exclude_patterns or include_patterns:
        pattern_info = []
        if exclude_patterns:
            pattern_type = "Regex" if use_regex else "Glob"
            pattern_info.append(
                f"{pattern_type} exclusion patterns: "
                f"{', '.join(str(p) for p in exclude_patterns)}"
            )
        if include_patterns:
            pattern_type = "Regex" if use_regex else "Glob"
            pattern_info.append(
                f"{pattern_type} inclusion patterns: "
                f"{', '.join(str(p) for p in include_patterns)}"
            )
        if pattern_info:
            pattern_panel = Panel(
                Text("\n".join(pattern_info)),
                title="Applied Patterns",
                border_style="blue",
            )
            console.print(pattern_panel)
    legend_panel = Panel(legend_text, border_style="dim")
    console.print(legend_panel)
    console.print(
        _render_side_by_side(
            console,
            Panel(
                tree1,
                title=Text(f"Directory 1: {root_base1}"),
                border_style="blue",
            ),
            Panel(
                tree2,
                title=Text(f"Directory 2: {root_base2}"),
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
    *,
    targets: _Targets | None = None,
) -> None:
    """Export a side-by-side directory comparison to an HTML file.

    Scans both directories with identical options and writes a standalone, responsive
    HTML document containing the highlighted comparison, a legend, and a summary of the
    settings used. Only HTML output is supported.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.
        format_type: Export format. Only ``"html"`` is supported.
        output_path: Path the HTML file is written to.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor (e.g. ``.gitignore``).
        exclude_extensions: File extensions to exclude. Normalized to a lowercase,
            dot-prefixed form before scanning.
        exclude_patterns: Glob or regex patterns to exclude.
        include_patterns: Glob or regex patterns to include. When given, only files
            whose names match one are kept, and a match overrides ignore-file rules for
            that file. They do not override *exclude_dirs*, *exclude_extensions*, or
            *exclude_patterns*.
        use_regex: Whether to treat the patterns as regular expressions instead of glob
            patterns.
        max_depth: Maximum depth to include, or ``0`` for unlimited.
        show_full_path: Whether to write absolute paths instead of bare filenames.
        spec: Resolved sorting and annotation directives. Defaults to a plain
            [`DisplayOptions`][recursivist.flags.DisplayOptions].
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        targets: The ``(target1, target2)`` pair already parsed from *dir1* and *dir2*
            with [`parse_github_url`][recursivist.github.parse_github_url] (``None`` for
            a local side), for callers that have it. Left as ``None``, the inputs are
            parsed here.

    Raises:
        ValueError: If *format_type* is not ``"html"``.
    """
    if format_type != "html":
        raise ValueError("Only HTML format is supported for comparison export")
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
    targets = _resolve_targets(dir1, dir2, targets)
    target1, target2 = targets
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
        targets=targets,
    )
    identity_spec = _identity_spec_for(target1, target2, spec)

    is_remote1 = target1 is not None
    is_remote2 = target2 is not None

    comparison_data = {
        "dir1": {
            "path": dir1,
            "name": _side_display_name(dir1, target1),
            "structure": structure1,
            "is_remote": is_remote1,
        },
        "dir2": {
            "path": dir2,
            "name": _side_display_name(dir2, target2),
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
    _export_comparison_to_html(comparison_data, output_path, icon_style)


def _export_comparison_to_html(
    comparison_data: dict[str, Any], output_path: str, icon_style: str = "emoji"
) -> None:
    """Write the comparison HTML document from prepared comparison data.

    Generates a responsive, styled HTML page with the two directory trees side by side
    and their differences highlighted, including any LOC, size, modification-time, or
    Git-status annotations enabled in the metadata.

    Args:
        comparison_data: Prepared comparison payload holding each directory's structure
            under ``"dir1"``/``"dir2"`` and the render settings under ``"metadata"``.
        output_path: Path the HTML file is written to.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
    """

    dir1_name = html.escape(comparison_data["dir1"]["name"])
    dir2_name = html.escape(comparison_data["dir2"]["name"])
    dir1_structure = comparison_data["dir1"]["structure"]
    dir2_structure = comparison_data["dir2"]["structure"]

    dir1_is_remote = comparison_data["dir1"].get("is_remote", False)
    dir2_is_remote = comparison_data["dir2"].get("is_remote", False)

    metadata = comparison_data.get("metadata", {})
    max_depth_info = ""
    max_depth_val = metadata.get("max_depth", 0)
    if max_depth_val > 0:
        level_word = "level" if max_depth_val == 1 else "levels"
        max_depth_info = (
            '<div class="info-block"><span class="info-label">Max Depth:</span> '
            f"{max_depth_val} {level_word}</div>"
        )
    path_info = ""
    if metadata.get("show_full_path"):
        path_info = (
            '<div class="info-block"><span class="info-label">Path Display:</span>'
            " Full paths shown</div>"
        )
    loc_info = ""
    if metadata.get("show_loc"):
        loc_info = (
            '<div class="info-block"><span class="info-label">Lines of Code:</span>'
            " LOC counts displayed</div>"
        )
    size_info = ""
    if metadata.get("show_size"):
        size_info = (
            '<div class="info-block"><span class="info-label">File Sizes:</span>'
            " File sizes displayed</div>"
        )
    mtime_info = ""
    if metadata.get("show_mtime"):
        mtime_info = (
            '<div class="info-block">'
            '<span class="info-label">Modification Times:</span>'
            " Timestamps displayed</div>"
        )
    git_status_info = ""
    if metadata.get("show_git_status"):
        git_status_info = (
            '<div class="info-block"><span class="info-label">Git Status:</span> '
            "Status markers displayed &mdash; "
            '<span class="git-badge">[U]</span> untracked, '
            '<span class="git-badge">[M]</span> modified, '
            '<span class="git-badge">[A]</span> added, '
            '<span class="git-badge">[D]</span> deleted</div>'
        )
    pattern_info_html = ""
    if metadata.get("exclude_patterns") or metadata.get("include_patterns"):
        pattern_type = metadata.get("pattern_type", "glob").capitalize()
        pattern_items = []
        if metadata.get("exclude_patterns"):
            patterns = [html.escape(p) for p in metadata.get("exclude_patterns", [])]
            pattern_items.append(
                f"<dt>Exclude {pattern_type} Patterns:</dt>"
                f"<dd>{', '.join(patterns)}</dd>"
            )
        if metadata.get("include_patterns"):
            patterns = [html.escape(p) for p in metadata.get("include_patterns", [])]
            pattern_items.append(
                f"<dt>Include {pattern_type} Patterns:</dt>"
                f"<dd>{', '.join(patterns)}</dd>"
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

    spec = DisplayOptions(
        sort_key=metadata.get("sort_key"),
        metrics=tuple(metadata.get("metrics", ())),
        show_git_status=metadata.get("show_git_status", False),
    )
    identity_spec = DisplayOptions(
        metrics=tuple(metadata.get("identity_metrics", spec.metrics)),
        show_git_status=metadata.get("identity_git", spec.show_git_status),
    )
    dir1_metrics = _side_metrics(spec.metrics, dir1_is_remote)
    dir2_metrics = _side_metrics(spec.metrics, dir2_is_remote)

    dir1_title = dir1_name + format_dir_metrics(dir1_structure, dir1_metrics)
    dir2_title = dir2_name + format_dir_metrics(dir2_structure, dir2_metrics)

    root_icon1 = get_icon(
        dir1_name,
        is_dir=True,
        style=icon_style,
        is_empty=not has_contents(dir1_structure),
    )
    root_icon2 = get_icon(
        dir2_name,
        is_dir=True,
        style=icon_style,
        is_empty=not has_contents(dir2_structure),
    )
    dir1_tree_html = _render_html_nodes(
        _ComparisonWalker.for_sides(
            spec, identity_spec, dir1_is_remote, dir2_is_remote, icon_style
        ).walk(dir1_structure, dir2_structure)
    )
    dir2_tree_html = _render_html_nodes(
        _ComparisonWalker.for_sides(
            spec, identity_spec, dir2_is_remote, dir1_is_remote, icon_style
        ).walk(dir2_structure, dir1_structure)
    )

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{dir1_name} vs {dir2_name}</title>
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
            h2 {{
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
            .symlink-loop {{
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
            .git-badge {{
                font-size: 0.8em;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
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
                {dir1_tree_html}
            </div>
            <div class="directory-tree">
                <h3>{root_icon2} {dir2_title}</h3>
                {dir2_tree_html}
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
