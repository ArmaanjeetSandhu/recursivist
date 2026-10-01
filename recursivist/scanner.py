"""Directory traversal.

Recursively walks a directory, applies the exclusion rules from
[`recursivist.filtering`][recursivist.filtering], collects optional per-file metrics
from [`recursivist.metrics`][recursivist.metrics], and returns the nested structure dict
consumed by the renderers and exporters.
"""

import logging
import os
from collections.abc import Iterator, Sequence
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

    Args:
        name: The directory's real name.

    Returns:
        The key to store the directory under.
    """
    if name in RESERVED_KEYS or name.startswith(_ESCAPE_PREFIX):
        return _ESCAPE_PREFIX + name
    return name


def _subdirectory_name(key: str) -> str:
    """Invert [`subdirectory_key`][recursivist.scanner.subdirectory_key]."""
    return key[len(_ESCAPE_PREFIX) :] if key.startswith(_ESCAPE_PREFIX) else key


def get_subdirectory(structure: dict[str, Any], name: str) -> Any | None:
    """Return the content of the subdirectory called *name*, or ``None`` if absent.

    Looks the directory up by its real name, so it never mistakes a reserved bookkeeping
    entry (such as the ``_files`` list) for a subdirectory of the same name.

    Args:
        structure: A directory-structure dict as produced by
            [`get_directory_structure`][recursivist.scanner.get_directory_structure].
        name: The subdirectory's real name.

    Returns:
        The subdirectory's structure, or ``None`` when *structure* has no such
        subdirectory.
    """
    return structure.get(subdirectory_key(name))


def _has_visible_entries(
    root_dir: str,
    exclude_dirs: Sequence[str],
    ignore_context: dict[str, Any],
    exclude_extensions: set[str],
    exclude_patterns: Sequence[str | Pattern[str]],
    include_patterns: Sequence[str | Pattern[str]],
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

    Returns:
        ``True`` if any child survives the exclusion rules.
    """
    try:
        items = os.listdir(root_dir)
    except PermissionError:
        logger.warning(f"Permission denied: {root_dir}")
        return False
    except Exception as e:
        logger.exception(f"Error reading directory {root_dir}: {e}")
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
        include_patterns: Glob or compiled-regex patterns to include, which override the
            exclusions.
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
        show_git_status,
        git_status_map,
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
    show_git_status: bool,
    git_status_map: dict[str, str] | None,
    ancestor_ids: frozenset[tuple[int, int]],
    pattern_tracker: PatternMatchTracker,
) -> tuple[dict[str, Any], set[str]]:
    """Scan one directory level for
    [`get_directory_structure`][recursivist.scanner.get_directory_structure].

    Takes the same arguments with their defaults already filled in, and recurses into
    subdirectories through `get_directory_structure` so the shared *pattern_tracker* is
    threaded through the whole walk.
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

    git_markers: dict[str, str] = {}
    if show_git_status and git_status_map is not None:
        current_prefix = current_path.replace(os.sep, "/") if current_path else ""
        for git_path, status in git_status_map.items():
            slash_idx = git_path.rfind("/")
            if slash_idx == -1:
                file_dir, fname = "", git_path
            else:
                file_dir, fname = git_path[:slash_idx], git_path[slash_idx + 1 :]
            if file_dir == current_prefix:
                git_markers[fname] = status
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
        ):
            truncated["_hidden_contents"] = True
        return truncated, extensions_set
    try:
        items = os.listdir(root_dir)
    except PermissionError:
        logger.warning(f"Permission denied: {root_dir}")
        return structure, extensions_set
    except Exception as e:
        logger.exception(f"Error reading directory {root_dir}: {e}")
        return structure, extensions_set
    for item in items:
        item_path = os.path.join(root_dir, item)
        if pattern_tracker.pending:
            pattern_tracker.observe(item_path, os.path.isdir(item_path))
        if item in exclude_dirs or should_exclude(
            item_path,
            ignore_context,
            exclude_extensions,
            exclude_patterns,
            include_patterns,
        ):
            continue
        if not os.path.isdir(item_path):
            _, ext = os.path.splitext(item)
            if "_files" not in structure:
                structure["_files"] = []
            file_loc = 0
            file_size = 0
            file_mtime = 0.0
            if sort_by_loc:
                file_loc = count_lines_of_code(item_path)
                total_loc += file_loc
            if sort_by_size:
                file_size = get_file_size(item_path)
                total_size += file_size
            if sort_by_mtime:
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
        if os.path.isdir(item_path):
            try:
                item_st = os.stat(item_path)
                item_id: tuple[int, int] | None = (item_st.st_dev, item_st.st_ino)
            except OSError:
                item_id = None
            if item_id is not None and item_id in child_ancestor_ids:
                logger.warning(
                    f"Skipping symlink cycle: {item_path} resolves to an ancestor"
                )
                structure[subdirectory_key(item)] = {"_symlink_loop": True}
                continue
            next_path = os.path.join(current_path, item) if current_path else item
            substructure, sub_extensions = get_directory_structure(
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
                show_git_status,
                git_status_map,
                child_ancestor_ids,
                pattern_tracker,
            )
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

    if show_git_status and git_markers:
        existing_names = {f.name for f in structure.get("_files", [])}

        for fname, status in git_markers.items():
            if status == "D" and fname not in existing_names:
                _, ext = os.path.splitext(fname)
                if ext:
                    extensions_set.add(ext.lower())
                if "_files" not in structure:
                    structure["_files"] = []
                abs_deleted = os.path.abspath(os.path.join(root_dir, fname)).replace(
                    os.sep, "/"
                )
                display = abs_deleted if show_full_path else fname
                structure["_files"].append(FileEntry(name=fname, path=display))

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
