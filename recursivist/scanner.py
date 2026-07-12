"""Directory traversal.

Recursively walks a directory, applies the exclusion rules from
:mod:`recursivist.filtering`, collects optional per-file metrics from
:mod:`recursivist.metrics`, and returns the nested structure dict consumed by
the renderers and exporters.
"""

import logging
import os
from collections.abc import Iterator, Sequence
from re import Pattern
from typing import Any

from recursivist._models import FileEntry
from recursivist.filtering import parse_ignore_file, should_exclude
from recursivist.metrics import (
    count_lines_of_code,
    get_file_mtime,
    get_file_size,
)

logger = logging.getLogger(__name__)


RESERVED_KEYS: frozenset[str] = frozenset(
    {"_files", "_loc", "_size", "_mtime", "_max_depth_reached", "_git_markers"}
)


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
) -> tuple[dict[str, Any], set[str]]:
    """Build a nested dictionary representing a directory structure.

    Recursively traverses *root_dir*, applying the exclusion rules and
    optionally collecting per-file metrics, and returns the nested mapping
    consumed by the renderers and exporters. Each subdirectory becomes a
    nested dict under its own name; a directory's files and aggregate metrics
    are stored under reserved keys.

    Reserved keys in the returned structure:

    - ``"_files"``: list of :class:`FileEntry` for the directory's files.
    - ``"_loc"``: total lines of code (when *sort_by_loc* is set).
    - ``"_size"``: total size in bytes (when *sort_by_size* is set).
    - ``"_mtime"``: latest modification time (when *sort_by_mtime* is set).
    - ``"_max_depth_reached"``: present when traversal stopped at *max_depth*.
    - ``"_git_markers"``: ``{filename: status_char}`` (when *show_git_status*
      is set).

    Args:
        root_dir: Directory to scan.
        exclude_dirs: Directory names to skip entirely.
        ignore_file: Name of an ignore file to honor within each directory
            (e.g. ``.gitignore``).
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        parent_ignore_patterns: Ignore files inherited from parent directories
            as a shallowest-first stack of ``(base_dir_relative_to_root,
            patterns)`` pairs. Each ignore file keeps its own anchoring so its
            patterns stay scoped to its subtree, matching Git. Set internally
            across the recursion.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include, which
            override the exclusions.
        max_depth: Maximum depth to traverse, or ``0`` for unlimited.
        current_depth: Current recursion depth. Set internally.
        current_path: Path of the current directory relative to the scan
            root. Set internally.
        show_full_path: Whether to store absolute paths instead of bare
            filenames.
        sort_by_loc: Whether to count and total lines of code.
        sort_by_size: Whether to measure and total file sizes.
        sort_by_mtime: Whether to record file modification times.
        show_git_status: Whether to annotate files with Git status markers.
        git_status_map: Pre-computed ``{rel_path: status_char}`` mapping, as
            returned by :func:`recursivist.git_status.get_git_status`.

    Returns:
        A ``(structure, extensions)`` tuple, where *structure* is the nested
        directory mapping and *extensions* is the set of lowercase file
        extensions encountered.
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_extensions is None:
        exclude_extensions = set()
    if exclude_patterns is None:
        exclude_patterns = []
    if include_patterns is None:
        include_patterns = []
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
        "current_dir": root_dir,
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
        return {"_max_depth_reached": True}, extensions_set
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
            if ext.lower() not in exclude_extensions:
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
            )
            if include_patterns and not (
                substructure.get("_files")
                or substructure.get("_max_depth_reached")
                or any(not k.startswith("_") for k in substructure)
            ):
                continue
            structure[item] = substructure
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

    Reserved bookkeeping keys (see :data:`RESERVED_KEYS`) are skipped, and
    entries are yielded in case-sensitive name order.

    Args:
        structure: A directory-structure dict as produced by
            :func:`get_directory_structure`.

    Yields:
        ``(subdirectory_name, subdirectory_content)`` pairs.
    """
    for name in sorted(k for k in structure if k not in RESERVED_KEYS):
        yield name, structure[name]
