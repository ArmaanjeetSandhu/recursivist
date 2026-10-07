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

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from recursivist._models import Directory, FileEntry
from recursivist.exporters.base import write_text
from recursivist.filtering import (
    PatternMatchTracker,
    compile_regex_patterns,
    normalize_extensions,
)
from recursivist.flags import METRIC_GIT, METRIC_MTIME, DisplayOptions
from recursivist.git_status import GitStatusError, get_git_status
from recursivist.github import (
    GitHubTarget,
    RepoCheckout,
    apply_github_urls,
    checkout_repository,
    get_github_token,
    parse_github_url,
    same_github_target,
)
from recursivist.icons import get_icon
from recursivist.metrics import (
    format_dir_metrics,
    format_metrics,
    format_metrics_suffix,
)
from recursivist.scanner import (
    get_directory_structure,
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
    handed down from there rather than being re-derived at each stage: *targets* is
    returned unchanged when given, and the inputs are parsed only when it is ``None``.
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
) -> Directory:
    """Scan a single already-resolved directory for one side of a comparison.

    Git status is looked up (and files annotated) only when *spec* requests it; when it
    cannot be read, a warning naming the cause is logged and the side is scanned without
    it. For GitHub sides, callers pass a spec with Git status and modification time
    already removed (see
    [`without_remote_unsupported`][recursivist.flags.DisplayOptions.without_remote_unsupported]).
    A hosted repository is never given Git markers or per-file timestamps.

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
        pattern_tracker: Shared record of which filters matched, used to report filters
            that matched nothing on either side.

    Returns:
        The scanned structure for this side.
    """
    need_git = spec.show_git_status or spec.sort_key == METRIC_GIT
    git_status_map: dict[str, str] | None = None
    if need_git:
        try:
            git_status_map = get_git_status(scan_dir)
        except GitStatusError as e:
            logger.warning("Git status unavailable for %s: %s", scan_dir, e)
    structure, _ = get_directory_structure(
        scan_dir,
        exclude_dirs=exclude_dirs,
        ignore_file=ignore_file,
        exclude_extensions=exclude_extensions,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
        max_depth=max_depth,
        show_full_path=show_full_path,
        collect_loc=spec.show_loc,
        collect_size=spec.show_size,
        collect_mtime=spec.show_mtime,
        git_status_map=git_status_map,
        pattern_tracker=pattern_tracker,
    )
    return structure


def _scan_sides(
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
) -> tuple[Directory, Directory, _Targets]:
    """Scan two inputs for comparison, each a local directory or GitHub URL.

    Each side is scanned with the same filtering and metric settings. A side may be a
    local directory or a GitHub repository URL; a GitHub side is downloaded and
    extracted to a temporary directory (removed before this function returns), scanned
    there, and — when *show_full_path* is set — has its file paths rewritten to GitHub
    blob URLs.

    The ``--ignore-file`` option, Git-status annotations, and modification-time
    annotations apply only to local directories. They are skipped for any GitHub side
    (its spec is adjusted via
    [`without_remote_unsupported`][recursivist.flags.DisplayOptions.without_remote_unsupported])
    and honored for a local side. When *both* sides are GitHub repositories the caller
    is expected to have already cleared these from *spec* as well.

    A GitHub URL that points at a file is scanned from the directory containing that
    file, which is only known once the repository has been downloaded; the returned
    targets carry that directory as their subpath, for callers to label each side after
    the directory actually scanned.

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
        A ``(structure1, structure2, targets)`` tuple: each input's structure, and the
        ``(target1, target2)`` pair as resolved by
        [`checkout_repository`][recursivist.github.checkout_repository] (``None`` for a
        local side).

    Any exclude/include filter that matched no entry on *either* side is logged as a
    warning once both scans finish.

    Raises:
        ValueError: If two GitHub URLs that point at files resolve to the same
            directory of the same commit, leaving nothing to compare.
    """
    if spec is None:
        spec = DisplayOptions()
    remote_spec = spec.without_remote_unsupported()

    target1, target2 = _resolve_targets(dir1, dir2, targets)
    tracker = PatternMatchTracker(
        exclude_dirs, exclude_extensions, exclude_patterns, include_patterns
    )

    def _checkout(
        stack: contextlib.ExitStack, target: GitHubTarget | None
    ) -> RepoCheckout | None:
        if target is None:
            return None
        return stack.enter_context(checkout_repository(target))

    def _side(raw: str, checkout: RepoCheckout | None) -> Directory:
        if checkout is None:
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
        checkout1 = _checkout(stack, target1)
        checkout2 = _checkout(stack, target2)
        resolved: _Targets = (
            checkout1.target if checkout1 is not None else None,
            checkout2.target if checkout2 is not None else None,
        )
        _reject_same_resolved_target((target1, target2), resolved)
        structure1 = _side(dir1, checkout1)
        structure2 = _side(dir2, checkout2)
    tracker.report("in either directory")
    return structure1, structure2, resolved


def _reject_same_resolved_target(parsed: _Targets, resolved: _Targets) -> None:
    """Raise if two GitHub inputs turned out to name the same directory.

    Two URLs that point at different files in one directory look like different targets
    until they are checked out, at which point each resolves to that shared directory.
    Comparing it against itself yields a diff in which everything is shared, so it is
    rejected here, before either side is scanned.

    Targets that the checkout left as parsed are not re-examined: it revealed nothing
    further about them, and whether such inputs are the same is the caller's call.

    Args:
        parsed: The ``(target1, target2)`` pair as parsed from the inputs.
        resolved: The same pair as checked out.

    Raises:
        ValueError: If both sides are GitHub targets, at least one was resolved from a
            file to its containing directory, and the resolved targets refer to the same
            repository, commit and directory.
    """
    resolved1, resolved2 = resolved
    if resolved1 is None or resolved2 is None or resolved == parsed:
        return
    if same_github_target(resolved1, resolved2, get_github_token()):
        where = f"'{resolved1.subpath}' in" if resolved1.subpath else "the root of"
        raise ValueError(
            f"cannot compare {where} '{resolved1.slug}' with itself (both URLs "
            "resolve to that directory); please provide two different directories "
            "or repositories"
        )


_GIT_BADGE_MARKERS = frozenset({"U", "M", "A", "D"})
"""Git status characters that render as a badge on a compared file."""

_SHARED = "shared"
_UNIQUE_THIS = "this"
_UNIQUE_OTHER = "other"


def _side_metrics(metrics: Sequence[str], is_remote: bool) -> tuple[str, ...]:
    """Return the metrics displayable for one side of a comparison.

    A remote side drops ``mtime``, which is meaningless for a hosted repository; a local
    side displays every requested metric. The display order of *metrics* is kept.
    """
    if is_remote:
        return tuple(m for m in metrics if m != METRIC_MTIME)
    return tuple(metrics)


def _git_badge_marker(markers: Mapping[str, str], name: str) -> str:
    """Return the badge-worthy Git status for *name*, or ``""``.

    That is the status character *markers* (the ``{filename: status_char}`` map for the
    file's side) holds for the bare filename, when it is one of `_GIT_BADGE_MARKERS`.
    Both renderers and the cross-side identity go through this one filter, so a marker
    never affects highlighting unless it would also be shown as a badge.
    """
    marker = markers.get(name, "")
    return marker if marker in _GIT_BADGE_MARKERS else ""


def _comparison_identity(
    entry: FileEntry,
    metrics: Sequence[str],
    show_git_status: bool,
    markers: Mapping[str, str],
    date_format: str = "relative",
    size_format: str = "iec",
) -> tuple[str, str, str]:
    """Return the key that decides whether a file matches one across the sides.

    Two identically named files count as the same entry only when they also present
    identically, so the identity combines the filename with the *displayed* annotations:

    * the numeric metrics named in *metrics* (LOC, size, mtime), rendered in the same
      order they are shown, and
    * the Git-status badge, when *show_git_status* is set.

    Because the identity mirrors the rendered annotation rather than the raw values, a
    difference in the key always corresponds to a visible difference in the tree (e.g.
    ``shared.py (3 lines)`` vs ``shared.py (1 line)``, or a ``[M]`` badge on only one
    side). Only the bare *name* is used for the filename component, never the full path,
    or full-path display would by itself make every file look unique.

    For the same reason, how finely modification times are told apart follows
    *date_format*: the ``"iso"`` form separates two files modified a second apart, while
    the ``"relative"`` form only separates them when the coarser text it shows differs.
    Sizes likewise are told apart as *size_format* writes them: two sizes that round to
    the same text in one set of units can differ in the other.

    Args:
        entry: The file whose identity is wanted.
        metrics: The numeric metrics being displayed, in display order.
        show_git_status: Whether the Git-status badge is displayed.
        markers: The ``{filename: status_char}`` map for *entry*'s own side.
        date_format: How the modification time is displayed, either ``"relative"`` or
            ``"iso"``.
        size_format: The units the size is displayed in, either ``"iec"`` or ``"si"``.

    Returns:
        A ``(name, metric_annotation, git_badge)`` tuple usable as a set key.
    """
    metric_annotation = format_metrics(
        entry.loc, entry.size, entry.mtime, metrics, date_format, size_format
    )
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
        """Whether the file is shown as deleted (struck through)."""
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
            self.spec.date_format,
            self.spec.size_format,
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
                entry.loc,
                entry.size,
                entry.mtime,
                metrics,
                self.spec.date_format,
                self.spec.size_format,
            ),
            git_marker=git_marker,
            uniqueness=uniqueness,
        )

    def _dir(
        self,
        name: str,
        content: Directory,
        this_content: Directory,
        other_content: Directory,
        uniqueness: str,
        metrics: Sequence[str],
        is_empty: bool,
    ) -> _DirNode:
        children: tuple[_Node, ...] | None
        if content.symlink_loop:
            children = ()
        elif content.max_depth_reached:
            children = None
        else:
            children = tuple(self.walk(this_content, other_content))
        return _DirNode(
            icon=get_icon(name, is_dir=True, style=self.icon_style, is_empty=is_empty),
            name=name,
            metrics_suffix=format_dir_metrics(
                content, metrics, self.spec.date_format, self.spec.size_format
            ),
            uniqueness=uniqueness,
            symlink_loop=content.symlink_loop,
            children=children,
        )

    def walk(self, structure: Directory, other_structure: Directory) -> list[_Node]:
        """Return the nodes for *structure*, compared against *other_structure*.

        Entries are ordered: this side's files (sorted), this side's directories, then
        files and directories that exist only on the other side. A directory that exists
        on one side only is walked against an empty
        [`Directory`][recursivist._models.Directory].

        Args:
            structure: The directory being rendered.
            other_structure: The directory being compared against.

        Returns:
            The comparison nodes at this level, each directory carrying its children.
        """
        loads_git = self._loads_git_markers
        sort_key = self.spec.sort_key
        markers: dict[str, str] = structure.git_markers if loads_git else {}
        other_markers: dict[str, str] = other_structure.git_markers if loads_git else {}
        nodes: list[_Node] = []

        other_ids = self._identities(other_structure.files, other_markers)
        for entry in sort_files_by_type(structure.files, sort_key, markers):
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
            other_match = other_structure.subdirectories.get(name)
            other_content = other_match if other_match is not None else Directory()
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

        this_ids = self._identities(structure.files, markers)
        nodes.extend(
            self._file(entry, other_markers, _UNIQUE_OTHER, self.other_metrics)
            for entry in sort_files_by_type(
                other_structure.files, sort_key, other_markers
            )
            if self._identity(entry, other_markers) not in this_ids
        )

        for name, other_content in iter_subdirectories(other_structure):
            if name in structure.subdirectories:
                continue
            nodes.append(
                self._dir(
                    name,
                    other_content,
                    Directory(),
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
    structure: Directory,
    other_structure: Directory,
    tree: Tree,
    spec: DisplayOptions,
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
    highlighted in red. File names are rendered without file-type-specific colors to let
    the green/red difference highlighting stand out. Files are ordered by
    ``spec.sort_key`` and metric annotations are appended in ``spec.metrics`` order.

    When ``spec.show_git_status`` is set, each file is followed by a plain Git-status
    badge — ``[U]`` untracked, ``[M]`` modified, ``[A]`` added, ``[D]`` deleted — read
    from the ``git_markers`` stored on *structure* (and on *other_structure* for
    entries unique to it). The badge is not color-coded; it trails the metric
    parenthetical, and deleted files are struck through.

    Two identically named files count as the same entry only when their *displayed*
    annotations also match (see `_comparison_identity`), so a differing metric or Git
    status marks them as unique to their side. *identity_spec* controls which
    annotations that match considers: it defaults to *spec*, but a caller comparing a
    local directory against a hosted repository passes
    ``spec.without_remote_unsupported()`` to exclude from the identity the annotations a
    remote side cannot provide (modification time, Git status). Those are still
    *displayed* per *spec*, but they do not split otherwise-matching files across the
    two sides.

    Sharing the traversal with the HTML export (see `_ComparisonWalker`) keeps both
    views in agreement on ordering, badges and highlighting.

    Args:
        structure: The directory being rendered.
        other_structure: The directory being compared against.
        tree: ``rich`` tree to add nodes to. Modified in place.
        spec: Resolved sorting and annotation directives.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        identity_spec: Directives governing which annotations contribute to cross-side
            file identity. Defaults to *spec*.
        this_is_remote: Whether the primary structure originates from a hosted
            repository.
        other_is_remote: Whether the compared structure originates from a hosted
            repository.
    """
    walker = _ComparisonWalker.for_sides(
        spec, identity_spec, this_is_remote, other_is_remote, icon_style
    )
    _render_rich_nodes(walker.walk(structure, other_structure), tree)


def _side_display_name(raw: str, target: GitHubTarget | None) -> str:
    """Return the label for one comparison side, local path or GitHub URL.

    For a GitHub URL this is the repository name (or the subpath's last segment); for a
    local path it is the directory's own name. *target* is the GitHub target for *raw*
    as checked out, or ``None`` for a local path. With it, a URL pointing at a file is
    named after the directory scanned in its place.
    """
    if target is not None:
        return target.display_name
    return os.path.basename(os.path.abspath(raw))


def _identity_spec_for(
    target1: GitHubTarget | None, target2: GitHubTarget | None, spec: DisplayOptions
) -> DisplayOptions:
    """Return the spec governing cross-side file identity for two inputs.

    This is the *identity_spec* passed to
    [`build_comparison_tree`][recursivist.compare.build_comparison_tree], which
    explains how it is applied. It is *spec* unchanged when both targets are ``None``
    (two local directories), or its
    [`without_remote_unsupported`][recursivist.flags.DisplayOptions.without_remote_unsupported]
    form when either side is a GitHub repository.
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
    exclude_extensions = normalize_extensions(exclude_extensions)
    compiled_exclude = compile_regex_patterns(exclude_patterns, use_regex)
    compiled_include = compile_regex_patterns(include_patterns, use_regex)
    targets = _resolve_targets(dir1, dir2, targets)
    structure1, structure2, (target1, target2) = _scan_sides(
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
            f"{root_icon1} {root_base1}"
            + format_dir_metrics(
                structure1, dir1_metrics, spec.date_format, spec.size_format
            ),
            style="bold",
        )
    )

    tree2 = Tree(
        Text(
            f"{root_icon2} {root_base2}"
            + format_dir_metrics(
                structure2, dir2_metrics, spec.date_format, spec.size_format
            ),
            style="bold",
        )
    )

    build_comparison_tree(
        structure1,
        structure2,
        tree1,
        spec,
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
    exclude_extensions = normalize_extensions(exclude_extensions)
    compiled_exclude = compile_regex_patterns(exclude_patterns, use_regex)
    compiled_include = compile_regex_patterns(include_patterns, use_regex)
    targets = _resolve_targets(dir1, dir2, targets)
    structure1, structure2, (target1, target2) = _scan_sides(
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
    _export_comparison_to_html(
        structure1,
        structure2,
        output_path,
        name1=_side_display_name(dir1, target1),
        name2=_side_display_name(dir2, target2),
        is_remote1=target1 is not None,
        is_remote2=target2 is not None,
        spec=spec,
        identity_spec=_identity_spec_for(target1, target2, spec),
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
        use_regex=use_regex,
        max_depth=max_depth,
        show_full_path=show_full_path,
        icon_style=icon_style,
    )


def _export_comparison_to_html(
    structure1: Directory,
    structure2: Directory,
    output_path: str,
    *,
    name1: str,
    name2: str,
    is_remote1: bool,
    is_remote2: bool,
    spec: DisplayOptions,
    identity_spec: DisplayOptions,
    exclude_patterns: Sequence[str],
    include_patterns: Sequence[str],
    use_regex: bool,
    max_depth: int,
    show_full_path: bool,
    icon_style: str,
) -> None:
    """Write the comparison HTML document for two scanned directories.

    Generates a responsive, styled HTML page with the two directory trees side by side
    and their differences highlighted, including any LOC, size, modification-time, or
    Git-status annotations enabled in *spec*, preceded by a summary of the settings the
    comparison was made with.

    Args:
        structure1: Scanned structure of the first directory.
        structure2: Scanned structure of the second directory.
        output_path: Path the HTML file is written to.
        name1: Display name of the first directory.
        name2: Display name of the second directory.
        is_remote1: Whether the first directory is a GitHub repository.
        is_remote2: Whether the second directory is a GitHub repository.
        spec: Resolved sorting and annotation directives.
        identity_spec: Directives governing which annotations contribute to cross-side
            file identity (see `_comparison_identity`).
        exclude_patterns: Exclusion patterns to list in the settings summary.
        include_patterns: Inclusion patterns to list in the settings summary.
        use_regex: Whether the patterns are regular expressions rather than globs.
        max_depth: Depth limit to report in the settings summary, or ``0`` for
            unlimited.
        show_full_path: Whether the trees show absolute paths, reported in the settings
            summary.
        icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
    """
    dir1_name = html.escape(name1)
    dir2_name = html.escape(name2)

    max_depth_info = ""
    if max_depth > 0:
        level_word = "level" if max_depth == 1 else "levels"
        max_depth_info = (
            '<div class="info-block"><span class="info-label">Max Depth:</span> '
            f"{max_depth} {level_word}</div>"
        )
    path_info = ""
    if show_full_path:
        path_info = (
            '<div class="info-block"><span class="info-label">Path Display:</span>'
            " Full paths shown</div>"
        )
    loc_info = ""
    if spec.show_loc:
        loc_info = (
            '<div class="info-block"><span class="info-label">Lines of Code:</span>'
            " LOC counts displayed</div>"
        )
    size_info = ""
    if spec.show_size:
        size_info = (
            '<div class="info-block"><span class="info-label">File Sizes:</span>'
            " File sizes displayed</div>"
        )
    mtime_info = ""
    if spec.show_mtime:
        mtime_info = (
            '<div class="info-block">'
            '<span class="info-label">Modification Times:</span>'
            " Timestamps displayed</div>"
        )
    git_status_info = ""
    if spec.show_git_status:
        git_status_info = (
            '<div class="info-block"><span class="info-label">Git Status:</span> '
            "Status markers displayed &mdash; "
            '<span class="git-badge">[U]</span> untracked, '
            '<span class="git-badge">[M]</span> modified, '
            '<span class="git-badge">[A]</span> added, '
            '<span class="git-badge">[D]</span> deleted</div>'
        )
    pattern_info_html = ""
    if exclude_patterns or include_patterns:
        pattern_type = "Regex" if use_regex else "Glob"
        pattern_items = []
        if exclude_patterns:
            patterns = [html.escape(p) for p in exclude_patterns]
            pattern_items.append(
                f"<dt>Exclude {pattern_type} Patterns:</dt>"
                f"<dd>{', '.join(patterns)}</dd>"
            )
        if include_patterns:
            patterns = [html.escape(p) for p in include_patterns]
            pattern_items.append(
                f"<dt>Include {pattern_type} Patterns:</dt>"
                f"<dd>{', '.join(patterns)}</dd>"
            )
        pattern_info_html = f"""
            <div class="pattern-info">
                <h3>Applied Patterns</h3>
                <dl>
                    {"".join(pattern_items)}
                </dl>
            </div>
            """

    dir1_metrics = _side_metrics(spec.metrics, is_remote1)
    dir2_metrics = _side_metrics(spec.metrics, is_remote2)

    dir1_title = dir1_name + format_dir_metrics(
        structure1, dir1_metrics, spec.date_format, spec.size_format
    )
    dir2_title = dir2_name + format_dir_metrics(
        structure2, dir2_metrics, spec.date_format, spec.size_format
    )

    root_icon1 = get_icon(
        dir1_name,
        is_dir=True,
        style=icon_style,
        is_empty=not has_contents(structure1),
    )
    root_icon2 = get_icon(
        dir2_name,
        is_dir=True,
        style=icon_style,
        is_empty=not has_contents(structure2),
    )
    dir1_tree_html = _render_html_nodes(
        _ComparisonWalker.for_sides(
            spec, identity_spec, is_remote1, is_remote2, icon_style
        ).walk(structure1, structure2)
    )
    dir2_tree_html = _render_html_nodes(
        _ComparisonWalker.for_sides(
            spec, identity_spec, is_remote2, is_remote1, icon_style
        ).walk(structure2, structure1)
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

    write_text(output_path, html_template)
