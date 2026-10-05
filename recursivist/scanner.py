"""Directory traversal.

Recursively walks a directory, applies the exclusion rules from
[`recursivist.filtering`][recursivist.filtering], collects optional per-file metrics
from [`recursivist.metrics`][recursivist.metrics], and returns the nested structure dict
consumed by the renderers and exporters.
"""

import logging
import os
from collections.abc import Iterator, Mapping, Sequence
from itertools import chain
from re import Pattern
from typing import Any

from recursivist._models import FileEntry
from recursivist.filtering import (
    PatternMatchTracker,
    parse_ignore_file,
    should_exclude,
)
from recursivist.metrics import (
    count_lines_of_code,
    get_file_mtime,
    get_file_size,
)

logger = logging.getLogger(__name__)


RESERVED_KEYS: frozenset[str] = frozenset(
    {
        "_files",
        "_loc",
        "_size",
        "_mtime",
        "_max_depth_reached",
        "_hidden_contents",
        "_symlink_loop",
        "_git_markers",
    }
)

_ESCAPE_PREFIX = "/"
"""Prefix marking a subdirectory key whose real name would clash with a reserved key.

A path separator can never occur in a file or directory name, so a key that starts with
``"/"`` is unambiguously an escaped subdirectory name and never a real one.
"""


def subdirectory_key(name: str) -> str:
    """Return the key a subdirectory called *name* is stored under in a structure dict.

    Subdirectories and the reserved bookkeeping keys share one mapping, so a directory
    whose name is itself a reserved key (e.g. a folder literally called ``_files``) is
    stored under an escaped key instead of overwriting that bookkeeping entry. Every
    other name is stored as-is. Read subdirectories back by their real names with
    [`iter_subdirectories`][recursivist.scanner.iter_subdirectories] and
    [`get_subdirectory`][recursivist.scanner.get_subdirectory].
    """
    if name in RESERVED_KEYS or name.startswith(_ESCAPE_PREFIX):
        return _ESCAPE_PREFIX + name
    return name


def _subdirectory_name(key: str) -> str:
    """Invert [`subdirectory_key`][recursivist.scanner.subdirectory_key]."""
    return key.removeprefix(_ESCAPE_PREFIX)


def get_subdirectory(structure: dict[str, Any], name: str) -> Any | None:
    """Return the content of the subdirectory called *name*, or ``None`` if absent.

    *structure* is a directory-structure dict as produced by
    [`get_directory_structure`][recursivist.scanner.get_directory_structure]. The
    directory is looked up by its real name, so a reserved bookkeeping entry (such as
    the ``_files`` list) is never mistaken for a subdirectory of the same name.
    """
    return structure.get(subdirectory_key(name))


class _DeletedEntries:
    """Files Git reports as deleted, indexed by the directory they were deleted from.

    A deleted file is no longer on disk, so a directory listing never returns it, and
    when it was the last file in its directory the directory is gone as well. This index
    lets the scanner list such entries alongside the ones on disk, so they pass through
    the same exclusion rules as everything else.

    Args:
        git_markers_by_dir: Git status markers grouped by directory, as returned by
            `_group_git_status`.
    """

    def __init__(self, git_markers_by_dir: Mapping[str, Mapping[str, str]]) -> None:
        self._files: dict[str, list[str]] = {}
        self._subdirs: dict[str, set[str]] = {}
        for directory, markers in git_markers_by_dir.items():
            deleted = [name for name, status in markers.items() if status == "D"]
            if not deleted:
                continue
            self._files[directory] = deleted
            while directory:
                parent, _, name = directory.rpartition("/")
                siblings = self._subdirs.setdefault(parent, set())
                if name in siblings:
                    break
                siblings.add(name)
                directory = parent

    def missing_from(self, root_dir: str, rel_dir: str) -> Iterator[tuple[str, bool]]:
        """Yield ``(name, is_dir)`` for the deleted entries a listing of *root_dir*
        lacks.

        These are the deleted files that are no longer on disk, and the subdirectories
        that held deleted files (at any depth) and are no longer on disk either. An
        entry that still exists is left to the directory listing.

        Args:
            root_dir: Filesystem path of the directory, which may itself be gone.
            rel_dir: The same directory relative to the scan root (``""`` for the root).
        """
        rel_dir = rel_dir.replace(os.sep, "/")
        for name in self._files.get(rel_dir, ()):
            path = os.path.join(root_dir, name)
            if os.path.isdir(path) or not os.path.lexists(path):
                yield name, False
        for name in sorted(self._subdirs.get(rel_dir, ())):
            if not os.path.isdir(os.path.join(root_dir, name)):
                yield name, True


def _has_visible_entries(
    root_dir: str,
    exclude_dirs: Sequence[str],
    ignore_context: dict[str, Any],
    exclude_extensions: set[str],
    exclude_patterns: Sequence[str | Pattern[str]],
    include_patterns: Sequence[str | Pattern[str]],
    deleted: _DeletedEntries | None = None,
    on_disk: bool = True,
) -> bool:
    """Return whether *root_dir* holds at least one non-excluded entry.

    Used at the depth limit, where the directory is not traversed but its renderers
    still need to know whether anything was left behind, so a truncated directory is not
    drawn as if it were empty. Only the immediate children are inspected, since that is
    enough to distinguish "nothing here" from "more below", without paying for a full
    recursive walk.

    Args:
        root_dir: Directory to peek into.
        exclude_dirs: Directory names to skip entirely.
        ignore_context: Ignore-file context for
            [`should_exclude`][recursivist.filtering.should_exclude].
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include.
        deleted: Index of the files Git reports as deleted, when Git status is shown.
            Deleted entries count like the ones on disk. A directory that exists only as
            the former home of deleted files is the one case that is followed downwards,
            because it is worth showing only if one of those files survives the
            exclusion rules.
        on_disk: Whether *root_dir* exists. ``False`` for a directory known only from
            *deleted*, which has nothing to list.

    Returns:
        ``True`` if any child survives the exclusion rules.
    """
    items: list[str] = []
    if on_disk:
        try:
            items = os.listdir(root_dir)
        except PermissionError:
            logger.warning("Permission denied: %s", root_dir)
            return False
        except Exception as e:
            logger.exception("Error reading directory %s: %s", root_dir, e)
            return False
    for item in items:
        item_path = os.path.join(root_dir, item)
        if item in exclude_dirs or should_exclude(
            item_path,
            ignore_context,
            exclude_extensions,
            exclude_patterns,
            include_patterns,
        ):
            continue
        return True
    if deleted is None:
        return False
    rel_dir = ignore_context.get("rel_dir", "")
    for item, is_dir in deleted.missing_from(root_dir, rel_dir):
        item_path = os.path.join(root_dir, item)
        if item in exclude_dirs or should_exclude(
            item_path,
            ignore_context,
            exclude_extensions,
            exclude_patterns,
            include_patterns,
            is_dir=is_dir,
        ):
            continue
        if not is_dir or _has_visible_entries(
            item_path,
            exclude_dirs,
            {**ignore_context, "rel_dir": os.path.join(rel_dir, item)},
            exclude_extensions,
            exclude_patterns,
            include_patterns,
            deleted,
            on_disk=False,
        ):
            return True
    return False


def has_contents(structure: Any) -> bool:
    """Return whether a directory-structure entry holds anything to display.

    A directory counts as non-empty when it has files, has subdirectories, or was cut
    short by the depth limit with contents left unexplored. Renderers use this to pick
    between the open and closed folder icons.

    Args:
        structure: A subtree of a structure dict as produced by
            [`get_directory_structure`][recursivist.scanner.get_directory_structure].

    Returns:
        ``True`` if the entry has visible contents.
    """
    if not isinstance(structure, dict):
        return False
    if structure.get("_max_depth_reached"):
        return bool(structure.get("_hidden_contents"))
    if structure.get("_symlink_loop"):
        return True
    if structure.get("_files"):
        return True
    return any(True for _ in iter_subdirectories(structure))


def _group_git_status(git_status_map: Mapping[str, str]) -> dict[str, dict[str, str]]:
    """Group a Git status map by the directory each path lives in.

    Done once per scan so that every directory can look its own markers up directly,
    instead of filtering the whole map again at each level.

    Args:
        git_status_map: ``{rel_path: status_char}`` with forward-slashed paths, as
            returned by
            [`recursivist.git_status.get_git_status`][recursivist.git_status.get_git_status].

    Returns:
        ``{directory: {filename: status_char}}``, where *directory* is forward-slashed
        and relative to the scan root (``""`` for the root itself).
    """
    grouped: dict[str, dict[str, str]] = {}
    for git_path, status in git_status_map.items():
        file_dir, _, fname = git_path.rpartition("/")
        grouped.setdefault(file_dir, {})[fname] = status
    return grouped


def get_directory_structure(
    root_dir: str,
    exclude_dirs: Sequence[str] | None = None,
    ignore_file: str | None = None,
    exclude_extensions: set[str] | None = None,
    parent_ignore_patterns: Sequence[tuple[str, tuple[str, ...]]] | None = None,
    exclude_patterns: Sequence[str | Pattern[str]] | None = None,
    include_patterns: Sequence[str | Pattern[str]] | None = None,
    max_depth: int = 0,
    current_depth: int = 0,
    current_path: str = "",
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
    show_git_status: bool = False,
    git_status_map: dict[str, str] | None = None,
    ancestor_ids: frozenset[tuple[int, int]] | None = None,
    pattern_tracker: PatternMatchTracker | None = None,
) -> tuple[dict[str, Any], set[str]]:
    """Build a nested dictionary representing a directory structure.

    Recursively traverses *root_dir*, applying the exclusion rules and optionally
    collecting per-file metrics, and returns the nested mapping consumed by the
    renderers and exporters. Each subdirectory becomes a nested dict under its own name
    (escaped via [`subdirectory_key`][recursivist.scanner.subdirectory_key] if that name
    is itself a reserved key); a directory's files and aggregate metrics are stored
    under reserved keys. Read subdirectories back with
    [`iter_subdirectories`][recursivist.scanner.iter_subdirectories] or
    [`get_subdirectory`][recursivist.scanner.get_subdirectory] rather than by raw key.

    Reserved keys in the returned structure:

    - ``"_files"``: list of [`FileEntry`][recursivist._models.FileEntry] for the
      directory's files.
    - ``"_loc"``: total lines of code (when *sort_by_loc* is set).
    - ``"_size"``: total size in bytes (when *sort_by_size* is set).
    - ``"_mtime"``: latest modification time (when *sort_by_mtime* is set).
    - ``"_max_depth_reached"``: present when traversal stopped at *max_depth*.
    - ``"_hidden_contents"``: present (and ``True``) alongside ``"_max_depth_reached"``
      when the untraversed directory is not empty, so renderers can still tell it apart
      from one that holds nothing.
    - ``"_symlink_loop"``: present (and ``True``) when a directory was not recursed into
      because it resolves to one of its own ancestors, i.e. a symlink (or other) cycle
      back up the tree.
    - ``"_git_markers"``: ``{filename: status_char}`` (when *show_git_status* is set).

    When *show_git_status* is set, files Git reports as deleted are listed even though
    they are no longer on disk, together with any directory that disappeared along with
    them. They are subject to the same exclusion rules as every other entry, and a
    deleted directory is listed only if at least one of its deleted files survives them.

    Args:
        root_dir: Directory to scan.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor within each directory (e.g.
            ``.gitignore``).
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        parent_ignore_patterns: Ignore files inherited from parent directories as a
            shallowest-first stack of ``(base_dir_relative_to_root, patterns)`` pairs.
            Each ignore file keeps its own anchoring so its patterns stay scoped to its
            subtree, matching Git. Set internally across the recursion.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include. When given, only
            files whose names match one are kept, and a match overrides ignore-file
            rules for that file. They do not override *exclude_dirs*,
            *exclude_extensions*, or *exclude_patterns*.
        max_depth: Maximum depth to traverse, or ``0`` for unlimited.
        current_depth: Current recursion depth. Set internally.
        current_path: Path of the current directory relative to the scan root. Set
            internally.
        show_full_path: Whether to store absolute paths instead of bare filenames.
        sort_by_loc: Whether to count and total lines of code.
        sort_by_size: Whether to measure and total file sizes.
        sort_by_mtime: Whether to record file modification times.
        show_git_status: Whether to annotate files with Git status markers.
        git_status_map: Pre-computed ``{rel_path: status_char}`` mapping, as returned by
            [`recursivist.git_status.get_git_status`][recursivist.git_status.get_git_status].
        ancestor_ids: ``(st_dev, st_ino)`` identities of the directories on the path
            from the scan root to (and including) *root_dir*, used to detect symlink
            cycles. Set internally across the recursion.
        pattern_tracker: Records which of the exclude/include filters matched a
            scanned entry. When omitted on the top-level call, one is created and each
            filter that matched nothing is logged as a warning once the scan finishes.
            Pass one explicitly to aggregate several scans (as a comparison does) and
            report it yourself.

    Returns:
        A ``(structure, extensions)`` tuple, where *structure* is the nested directory
        mapping and *extensions* is the set of lowercase file extensions encountered.
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_extensions is None:
        exclude_extensions = set()
    if exclude_patterns is None:
        exclude_patterns = []
    if include_patterns is None:
        include_patterns = []
    if ancestor_ids is None:
        ancestor_ids = frozenset()
    owns_tracker = pattern_tracker is None and current_depth == 0
    if pattern_tracker is None:
        pattern_tracker = PatternMatchTracker(
            exclude_dirs, exclude_extensions, exclude_patterns, include_patterns
        )
    git_markers_by_dir = (
        _group_git_status(git_status_map)
        if show_git_status and git_status_map is not None
        else None
    )
    structure, extensions_set = _scan_level(
        root_dir,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        parent_ignore_patterns,
        exclude_patterns,
        include_patterns,
        max_depth,
        current_depth,
        current_path,
        show_full_path,
        sort_by_loc,
        sort_by_size,
        sort_by_mtime,
        git_markers_by_dir,
        _DeletedEntries(git_markers_by_dir) if git_markers_by_dir is not None else None,
        ancestor_ids,
        pattern_tracker,
    )
    if owns_tracker:
        pattern_tracker.report()
    return structure, extensions_set


def _scan_level(
    root_dir: str,
    exclude_dirs: Sequence[str],
    ignore_file: str | None,
    exclude_extensions: set[str],
    parent_ignore_patterns: Sequence[tuple[str, tuple[str, ...]]] | None,
    exclude_patterns: Sequence[str | Pattern[str]],
    include_patterns: Sequence[str | Pattern[str]],
    max_depth: int,
    current_depth: int,
    current_path: str,
    show_full_path: bool,
    sort_by_loc: bool,
    sort_by_size: bool,
    sort_by_mtime: bool,
    git_markers_by_dir: Mapping[str, dict[str, str]] | None,
    deleted: _DeletedEntries | None,
    ancestor_ids: frozenset[tuple[int, int]],
    pattern_tracker: PatternMatchTracker,
    on_disk: bool = True,
) -> tuple[dict[str, Any], set[str]]:
    """Scan one directory level for
    [`get_directory_structure`][recursivist.scanner.get_directory_structure].

    Takes the same arguments with their defaults already filled in, except that the Git
    status map arrives pre-grouped by directory (see `_group_git_status`) along with the
    matching *deleted* index, or both as ``None`` when Git status is not wanted.
    Recurses into subdirectories directly, so that grouping and the shared
    *pattern_tracker* are reused for the whole walk.

    The entries of a level are the ones on disk followed by the ones Git reports as
    deleted from it. Each entry is classified and filtered exactly once: files are
    recorded as they are met, and the surviving subdirectories are queued and descended
    into afterwards. *on_disk* is ``False`` for a directory that is itself gone and is
    being walked only for its deleted files.
    """
    ignore_stack: list[tuple[str, tuple[str, ...]]] = (
        list(parent_ignore_patterns) if parent_ignore_patterns else []
    )
    if ignore_file:
        current_ignore_patterns = parse_ignore_file(os.path.join(root_dir, ignore_file))
        if current_ignore_patterns:
            ignore_stack = [
                *ignore_stack,
                (current_path, tuple(current_ignore_patterns)),
            ]
    ignore_context = {
        "pattern_stack": ignore_stack,
        "rel_dir": current_path,
    }
    structure: dict[str, Any] = {}
    extensions_set: set[str] = set()
    total_loc = 0
    total_size = 0
    latest_mtime = 0.0
    if max_depth > 0 and current_depth >= max_depth:
        pattern_tracker.depth_limited = True
        truncated: dict[str, Any] = {"_max_depth_reached": True}
        if _has_visible_entries(
            root_dir,
            exclude_dirs,
            ignore_context,
            exclude_extensions,
            exclude_patterns,
            include_patterns,
            deleted,
            on_disk,
        ):
            truncated["_hidden_contents"] = True
        return truncated, extensions_set
    items: list[str] = []
    if on_disk:
        try:
            items = os.listdir(root_dir)
        except PermissionError:
            logger.warning("Permission denied: %s", root_dir)
            return structure, extensions_set
        except Exception as e:
            logger.exception("Error reading directory %s: %s", root_dir, e)
            return structure, extensions_set
    entries: Iterator[tuple[str, bool, bool]] = (
        (item, os.path.isdir(os.path.join(root_dir, item)), True) for item in items
    )
    if deleted is not None:
        entries = chain(
            entries,
            (
                (item, is_dir, False)
                for item, is_dir in deleted.missing_from(root_dir, current_path)
            ),
        )
    subdirectories: list[tuple[str, str, bool]] = []
    for item, is_dir, exists in entries:
        item_path = os.path.join(root_dir, item)
        if pattern_tracker.pending:
            pattern_tracker.observe(item_path, is_dir)
        if item in exclude_dirs or should_exclude(
            item_path,
            ignore_context,
            exclude_extensions,
            exclude_patterns,
            include_patterns,
            is_dir=is_dir,
        ):
            continue
        if is_dir:
            subdirectories.append((item, item_path, exists))
        else:
            _, ext = os.path.splitext(item)
            if "_files" not in structure:
                structure["_files"] = []
            file_loc = 0
            file_size = 0
            file_mtime = 0.0
            if exists and sort_by_loc:
                file_loc = count_lines_of_code(item_path)
                total_loc += file_loc
            if exists and sort_by_size:
                file_size = get_file_size(item_path)
                total_size += file_size
            if exists and sort_by_mtime:
                file_mtime = get_file_mtime(item_path)
                latest_mtime = max(latest_mtime, file_mtime)
            if show_full_path:
                display = os.path.abspath(item_path).replace(os.sep, "/")
            else:
                display = item
            structure["_files"].append(
                FileEntry(
                    name=item,
                    path=display,
                    loc=file_loc,
                    size=file_size,
                    mtime=file_mtime,
                )
            )
            if ext:
                extensions_set.add(ext.lower())
    try:
        st = os.stat(root_dir)
        child_ancestor_ids = ancestor_ids | {(st.st_dev, st.st_ino)}
    except OSError:
        child_ancestor_ids = ancestor_ids
    for item, item_path, exists in subdirectories:
        try:
            item_st = os.stat(item_path)
            item_id: tuple[int, int] | None = (item_st.st_dev, item_st.st_ino)
        except OSError:
            item_id = None
        if item_id is not None and item_id in child_ancestor_ids:
            logger.warning(
                "Skipping symlink cycle: %s resolves to an ancestor", item_path
            )
            structure[subdirectory_key(item)] = {"_symlink_loop": True}
            continue
        next_path = os.path.join(current_path, item) if current_path else item
        substructure, sub_extensions = _scan_level(
            item_path,
            exclude_dirs,
            ignore_file,
            exclude_extensions,
            ignore_stack,
            exclude_patterns,
            include_patterns,
            max_depth,
            current_depth + 1,
            next_path,
            show_full_path,
            sort_by_loc,
            sort_by_size,
            sort_by_mtime,
            git_markers_by_dir,
            deleted,
            child_ancestor_ids,
            pattern_tracker,
            on_disk=exists,
        )
        if not exists and not has_contents(substructure):
            continue
        if include_patterns and not (
            substructure.get("_files")
            or substructure.get("_max_depth_reached")
            or any(True for _ in iter_subdirectories(substructure))
        ):
            continue
        structure[subdirectory_key(item)] = substructure
        extensions_set.update(sub_extensions)
        if sort_by_loc and "_loc" in substructure:
            total_loc += substructure["_loc"]
        if sort_by_size and "_size" in substructure:
            total_size += substructure["_size"]
        if sort_by_mtime and "_mtime" in substructure:
            latest_mtime = max(latest_mtime, substructure["_mtime"])
    if sort_by_loc:
        structure["_loc"] = total_loc
    if sort_by_size:
        structure["_size"] = total_size
    if sort_by_mtime:
        structure["_mtime"] = latest_mtime

    git_markers = (
        git_markers_by_dir.get(current_path.replace(os.sep, "/"))
        if git_markers_by_dir is not None
        else None
    )
    if git_markers:
        structure["_git_markers"] = git_markers

    return structure, extensions_set


def iter_subdirectories(structure: dict[str, Any]) -> Iterator[tuple[str, Any]]:
    """Yield ``(name, content)`` for each real subdirectory in *structure*.

    Reserved bookkeeping keys (see `RESERVED_KEYS`) are skipped, escaped keys (see
    [`subdirectory_key`][recursivist.scanner.subdirectory_key]) are yielded under their
    real names, and entries are yielded in case-sensitive name order.

    Args:
        structure: A directory-structure dict as produced by
            [`get_directory_structure`][recursivist.scanner.get_directory_structure].

    Yields:
        ``(subdirectory_name, subdirectory_content)`` pairs.
    """
    entries = (
        (_subdirectory_name(key), content)
        for key, content in structure.items()
        if key not in RESERVED_KEYS
    )
    yield from sorted(entries, key=lambda entry: entry[0])


def collect_extensions(structure: dict[str, Any]) -> set[str]:
    """Return the lowercase file extensions of every file in *structure*.

    Walks the whole structure and gathers the same set that
    [`get_directory_structure`][recursivist.scanner.get_directory_structure] returns
    alongside it, for callers that hold only the structure.

    Args:
        structure: A directory-structure dict as produced by
            [`get_directory_structure`][recursivist.scanner.get_directory_structure].

    Returns:
        The set of extensions, each lowercase with its leading dot (e.g. ``".py"``).
        Files without an extension contribute nothing.
    """
    extensions: set[str] = set()
    for entry in structure.get("_files", []):
        _, ext = os.path.splitext(entry.name)
        if ext:
            extensions.add(ext.lower())
    for _, content in iter_subdirectories(structure):
        if isinstance(content, dict):
            extensions.update(collect_extensions(content))
    return extensions
