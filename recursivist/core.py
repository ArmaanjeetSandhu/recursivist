"""
Core functionality for the Recursivist directory visualization tool.

This module provides the fundamental components for building, filtering, displaying, and exporting directory structures. It handles directory traversal, pattern matching, color coding, file statistics calculation, and tree construction.

Key components:
- Directory structure parsing and representation
- Pattern-based filtering (gitignore, glob, regex)
- File extension color coding
- Tree visualization with rich formatting
- Lines of code counting
- File size calculation and formatting
- Modification time retrieval and formatting
- File name similarity grouping (difflib-based)
- Maximum depth limiting
"""

import colorsys
import datetime
import fnmatch
import hashlib
import logging
import math
import os
import re
from collections.abc import Iterator, Sequence
from datetime import datetime as dt
from difflib import SequenceMatcher
from functools import cache
from re import Pattern
from typing import Any, cast

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from recursivist._models import FileEntry
from recursivist.icons import get_icon

logger = logging.getLogger(__name__)


def parse_ignore_file(ignore_file_path: str) -> list[str]:
    """Parse an ignore file (like .gitignore) and return patterns.

    Reads an ignore file and extracts patterns for excluding files and directories. Handles comments and trailing slashes in directories.

    Args:
        ignore_file_path: Path to the ignore file

    Returns:
        List of patterns to ignore
    """
    if not os.path.exists(ignore_file_path):
        return []
    patterns = []
    with open(ignore_file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def get_git_status(directory: str) -> dict[str, str]:
    """Get Git status for files relative to a given directory.

    Runs ``git status --porcelain -z`` from the repository root and maps every
    changed/untracked path back to a path relative to *directory*, filtering
    out files that live outside of it.

    Status characters returned:
    - ``'U'``: Untracked (``??`` in porcelain output)
    - ``'M'``: Modified (working-tree or staged modification)
    - ``'A'``: Added / staged for the first time (includes renames)
    - ``'D'``: Deleted (working-tree or staged deletion)

    Args:
        directory: Absolute path to the directory being visualised. Must be
            inside a Git repository.

    Returns:
        ``{relative_path: status_char}`` where *relative_path* uses forward
        slashes regardless of OS, or an empty dict when Git is unavailable or
        the directory is not tracked.
    """
    import subprocess

    try:
        root_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory,
            capture_output=True,
            text=True,
        )
        if root_result.returncode != 0:
            return {}
        git_root = root_result.stdout.strip()

        status_result = subprocess.run(
            ["git", "status", "--porcelain", "-z"],
            cwd=git_root,
            capture_output=True,
            text=True,
        )
        if status_result.returncode != 0:
            return {}

        status_map: dict[str, str] = {}
        records = status_result.stdout.split("\0")
        i = 0
        while i < len(records):
            entry = records[i]
            i += 1
            if len(entry) < 4:
                continue
            xy = entry[:2]
            path = entry[3:]

            x, y = xy[0], xy[1]
            if x == "R" or x == "C":
                i += 1
            if x == "?" and y == "?":
                status = "U"
            elif x == "D" or y == "D":
                status = "D"
            elif x == "A" or x == "R":
                status = "A"
            elif x == "M" or y == "M":
                status = "M"
            else:
                status = "M"

            abs_file = os.path.normpath(
                os.path.join(git_root, path.replace("/", os.sep))
            )
            try:
                rel = os.path.relpath(abs_file, directory)
                if not rel.startswith(".."):
                    status_map[rel.replace(os.sep, "/")] = status
            except ValueError:
                pass

        return status_map
    except Exception as e:
        logger.debug(f"Could not get git status for {directory}: {e}")
        return {}


def compile_regex_patterns(
    patterns: Sequence[str], is_regex: bool = False
) -> list[str | Pattern[str]]:
    """Convert patterns to compiled regex objects when appropriate.

    When is_regex is True, compiles string patterns into regex pattern objects for efficient matching. For invalid regex patterns, logs a warning and keeps them as strings.

    Args:
        patterns: List of patterns to compile
        is_regex: Whether the patterns should be treated as regex (True) or glob patterns (False)

    Returns:
        List of patterns (strings for glob patterns or compiled regex objects)
    """
    if not is_regex:
        return cast(list[str | Pattern[str]], patterns)
    compiled_patterns: list[str | Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled_patterns.append(re.compile(pattern))
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            compiled_patterns.append(pattern)
    return compiled_patterns


def _gitignore_glob_to_regex(glob: str, anchored: bool) -> str:
    """Translate a gitignore glob (no leading '!'/'/' and no trailing '/') into
    a regex for a forward-slash path.

    '*' matches anything but '/', '**' crosses '/', '?' is one non-'/' char, and
    '[...]' is a character class. Anchored patterns must match from the start of
    the path; floating patterns may match at any directory depth.
    """
    i, n = 0, len(glob)
    out: list[str] = []
    while i < n:
        c = glob[i]
        if c == "*":
            star = 0
            while i < n and glob[i] == "*":
                star += 1
                i += 1
            if star >= 2:
                if i < n and glob[i] == "/":
                    out.append("(?:.*/)?")
                    i += 1
                else:
                    out.append(".*")
            else:
                out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[":
            j = i + 1
            if j < n and glob[j] in ("!", "^"):
                j += 1
            if j < n and glob[j] == "]":
                j += 1
            while j < n and glob[j] != "]":
                j += 1
            if j >= n:
                out.append(re.escape("["))
                i += 1
            else:
                cls = glob[i + 1 : j]
                if cls.startswith("!"):
                    cls = "^" + cls[1:]
                out.append("[" + cls + "]")
                i = j + 1
        elif c == "/":
            out.append("/")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    body = "".join(out)
    prefix = r"\A" if anchored else r"(?:\A|.*/)"
    return prefix + body + r"(?:/|\Z)"


@cache
def _compile_ignore_pattern(body: str) -> tuple[Pattern[str], bool] | None:
    """Compile a gitignore pattern body (the part after any leading '!').

    Returns ``(regex, dir_only)`` or ``None`` for an empty pattern. The regex is
    searched against a path relative to the ignore file's directory, expressed
    with forward slashes and no leading slash. ``dir_only`` patterns (trailing
    '/') match directories only. Cached so each unique pattern compiles once.
    """
    if body.startswith(("\\#", "\\!")):
        body = body[1:]
    dir_only = body.endswith("/")
    if dir_only:
        body = body[:-1]
    anchored = "/" in body
    if body.startswith("/"):
        body = body[1:]
    if not body:
        return None
    try:
        return re.compile(_gitignore_glob_to_regex(body, anchored)), dir_only
    except re.error:
        return None


def should_exclude(
    path: str,
    ignore_context: dict[str, Any],
    exclude_extensions: set[str] | None = None,
    exclude_patterns: Sequence[str | Pattern[str]] | None = None,
    include_patterns: Sequence[str | Pattern[str]] | None = None,
) -> bool:
    """Determine if a path should be excluded based on filtering rules.

    Logic to handle priority between include and exclude patterns:
    1. If include_patterns exist and NONE match, EXCLUDE the path
    2. If exclude_patterns match, EXCLUDE the path (overrides include patterns)
    3. If file extension is in exclude_extensions, EXCLUDE the path
    4. If a matching include pattern exists, INCLUDE the path (overrides gitignore patterns)
    5. If gitignore-style patterns match, follow their rules (including negations)

    Args:
        path: Path to check for exclusion
        ignore_context: Dictionary with 'patterns' and 'current_dir' keys
        exclude_extensions: Set of file extensions to exclude
        exclude_patterns: List of patterns (glob or regex) to exclude
        include_patterns: List of patterns (glob or regex) to include (overrides gitignore exclusions)
    Returns:
        True if path should be excluded, False otherwise
    """
    patterns = ignore_context.get("patterns", [])
    current_dir = ignore_context.get("current_dir", os.path.dirname(path))
    rel_path = os.path.relpath(path, current_dir)
    if os.name == "nt":
        rel_path = rel_path.replace("\\", "/")
    basename = os.path.basename(path)
    if include_patterns and not os.path.isdir(path):
        included = False
        for pattern in include_patterns:
            if isinstance(pattern, Pattern):
                if pattern.search(rel_path) or pattern.search(basename):
                    included = True
                    break
            else:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                    basename, pattern
                ):
                    included = True
                    break
        if not included:
            return True
    if exclude_patterns:
        for pattern in exclude_patterns:
            if isinstance(pattern, Pattern):
                if pattern.search(rel_path) or pattern.search(basename):
                    return True
            else:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                    basename, pattern
                ):
                    return True
    if exclude_extensions and os.path.isfile(path):
        _, ext = os.path.splitext(path)
        if ext.lower() in exclude_extensions:
            return True
    if include_patterns:
        return False
    if not patterns:
        return False
    rel_dir = ignore_context.get("rel_dir", "")
    rel_to_root = (f"{rel_dir}/{basename}" if rel_dir else basename).replace("\\", "/")
    rel_to_root = rel_to_root.lstrip("/")
    is_dir = os.path.isdir(path)
    excluded = False
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern:
            continue
        negated = pattern.startswith("!")
        compiled = _compile_ignore_pattern(pattern[1:] if negated else pattern)
        if compiled is None:
            continue
        regex, dir_only = compiled
        if dir_only and not is_dir:
            continue
        if regex.search(rel_to_root):
            excluded = not negated
    return excluded


_EXTENSION_COLORS: dict[str, str] = {}


def color_distance(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
    """Calculate the perceptual distance between two RGB colors.

    Uses a weighted Euclidean distance formula that approximates human color
    perception by emphasising the green channel over red and blue.

    Args:
        color1: First color as an ``(r, g, b)`` tuple with component values
            in the range ``0``\u2013``255``.
        color2: Second color as an ``(r, g, b)`` tuple with component values
            in the range ``0``\u2013``255``.

    Returns:
        A non-negative float representing the perceptual distance; ``0.0``
        means the colors are identical and larger values indicate greater
        visual difference.
    """
    r1, g1, b1 = [x / 255 for x in color1]
    r2, g2, b2 = [x / 255 for x in color2]
    r_weight, g_weight, b_weight = 0.3, 0.59, 0.11
    dist = math.sqrt(
        r_weight * (r1 - r2) ** 2
        + g_weight * (g1 - g2) ** 2
        + b_weight * (b1 - b2) ** 2
    )
    return dist


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a CSS hex color string to an ``(r, g, b)`` tuple.

    Args:
        hex_color: Six-digit hex color string, optionally prefixed with
            ``'#'`` (e.g., ``"#FF5733"`` or ``"FF5733"``).

    Returns:
        A three-tuple of integers ``(red, green, blue)`` in the range
        ``0``–``255``.
    """
    hex_color = hex_color.lstrip("#")
    return cast(
        tuple[int, int, int], tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    )


def generate_color_for_extension(extension: str) -> str:
    """Generate a consistent color for a file extension with collision detection.

    Creates a deterministic color based on the extension string using a hash function. The same extension will always get the same color within a session, and different extensions get visually distinct colors.

    Args:
        extension: File extension (with or without leading dot)

    Returns:
        Hex color code (e.g., "#FF5733")
    """
    global _EXTENSION_COLORS
    if not extension:
        return "#FFFFFF"
    normalized_ext = extension
    if not extension.startswith("."):
        normalized_ext = "." + extension
    if extension in _EXTENSION_COLORS:
        return _EXTENSION_COLORS[extension]
    if extension != normalized_ext and normalized_ext in _EXTENSION_COLORS:
        color = _EXTENSION_COLORS[normalized_ext]
        _EXTENSION_COLORS[extension] = color
        return color
    hash_bytes = hashlib.md5(normalized_ext.encode(), usedforsecurity=False).digest()
    hue_int = int.from_bytes(hash_bytes[0:4], byteorder="big")
    hue = (hue_int % 360) / 360.0
    sat_int = hash_bytes[4]
    saturation = 0.65 + (sat_int % 26) / 100.0
    val_int = hash_bytes[5]
    value = 0.85 + (val_int % 16) / 100.0
    min_acceptable_distance = 0.15
    max_attempts = 15
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    initial_color = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
    if not _EXTENSION_COLORS:
        hex_color = "#{:02x}{:02x}{:02x}".format(*initial_color)
        _EXTENSION_COLORS[extension] = hex_color
        if extension != normalized_ext:
            _EXTENSION_COLORS[normalized_ext] = hex_color
        return hex_color
    best_color = initial_color
    best_min_distance = 0.0
    for attempt in range(max_attempts):
        test_hue = (hue + (attempt * 0.1)) % 1.0
        test_sat = min(1.0, saturation + (attempt * 0.02))
        test_val = max(0.8, value - (attempt * 0.01))
        rgb = colorsys.hsv_to_rgb(test_hue, test_sat, test_val)
        test_color = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        min_distance = float("inf")
        for existing_color in _EXTENSION_COLORS.values():
            existing_rgb = hex_to_rgb(existing_color)
            distance = color_distance(test_color, existing_rgb)
            min_distance = min(min_distance, distance)
        if min_distance > best_min_distance:
            best_min_distance = min_distance
            best_color = test_color
        if min_distance >= min_acceptable_distance:
            break
    hex_color = "#{:02x}{:02x}{:02x}".format(*best_color)
    _EXTENSION_COLORS[extension] = hex_color
    if extension != normalized_ext:
        _EXTENSION_COLORS[normalized_ext] = hex_color
    return hex_color


def get_directory_structure(
    root_dir: str,
    exclude_dirs: Sequence[str] | None = None,
    ignore_file: str | None = None,
    exclude_extensions: set[str] | None = None,
    parent_ignore_patterns: Sequence[str] | None = None,
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

    Recursively traverses the file system applying filters and collecting statistics.

    The resulting structure contains:
    - Hierarchical representation of directories and files
    - Optional statistics (lines of code, sizes, modification times)
    - Filtered entries based on various exclusion patterns

    Special dictionary keys:
    - "_files": List of files in the directory
    - "_loc": Total lines of code (if sort_by_loc is True)
    - "_size": Total size in bytes (if sort_by_size is True)
    - "_mtime": Latest modification timestamp (if sort_by_mtime is True)
    - "_max_depth_reached": Flag indicating max depth was reached
    - "_git_markers": Dict mapping filename to Git status char (if show_git_status is True)

    Args:
        root_dir: Root directory path to start from
        exclude_dirs: List of directory names to exclude
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude
        parent_ignore_patterns: Patterns from parent directories' ignore files
        exclude_patterns: List of patterns (glob or regex) to exclude
        include_patterns: List of patterns (glob or regex) to include (overrides exclusions)
        max_depth: Maximum depth to traverse (0 for unlimited)
        current_depth: Current depth in the directory tree (for internal recursion)
        current_path: Current path for full path display (for internal recursion)
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to calculate and track lines of code counts
        sort_by_size: Whether to calculate and track file sizes
        sort_by_mtime: Whether to track file modification times
        show_git_status: Whether to annotate files with Git status markers
        git_status_map: Pre-computed {rel_path: status_char} mapping (from get_git_status)

    Returns:
        Tuple of (structure dictionary, set of file extensions found)
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_extensions is None:
        exclude_extensions = set()
    if exclude_patterns is None:
        exclude_patterns = []
    if include_patterns is None:
        include_patterns = []
    ignore_patterns = list(parent_ignore_patterns) if parent_ignore_patterns else []
    if ignore_file and os.path.exists(os.path.join(root_dir, ignore_file)):
        current_ignore_patterns = parse_ignore_file(os.path.join(root_dir, ignore_file))
        ignore_patterns.extend(current_ignore_patterns)
    ignore_context = {
        "patterns": ignore_patterns,
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
                ignore_patterns,
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
        existing_names: set[str] = set()
        for f in structure.get("_files", []):
            if isinstance(f, FileEntry):
                name = f.name
            elif isinstance(f, tuple):
                name = f[0]
            else:
                name = f
            existing_names.add(name)

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


def sort_files_by_similarity(files: Sequence[Any]) -> list[FileEntry]:
    """Order files so that similarly named files sit next to each other.

    Unlike the LOC/size/mtime metrics, name similarity is *relational*: it
    depends on how a file's name compares to the others rather than on any
    single measured value, so it cannot be expressed as a ``sorted`` key.
    Instead this builds a greedy nearest-neighbour chain:

    1. Entries are seeded in case-insensitive name order and the
       alphabetically-first name becomes the start of the chain. Using a
       fixed, name-derived anchor makes the result deterministic and stable
       across runs (the same directory always yields the same order).
    2. Repeatedly, the not-yet-placed entry whose name is most similar to the
       most recently placed name is appended. Similarity is the
       :class:`difflib.SequenceMatcher` ratio computed case-insensitively on
       the full filename (extension included), so ``main.py``/``main.js`` and
       ``test_api.py``/``test_api.js`` naturally cluster.
    3. Ratio ties are broken by case-insensitive name order: because the
       candidates are kept alphabetically sorted and the best match is only
       replaced on a strictly greater ratio, the alphabetically-first of any
       tied group wins.

    This is a heuristic (locally greedy) ordering rather than a globally
    optimal grouping, which is the appropriate trade-off for a directory
    listing: each directory holds relatively few files, so the ``O(n^2)``
    pairwise comparisons are cheap, and the result reliably places obvious
    name-siblings adjacent to one another.

    Inputs may be :class:`FileEntry` instances, bare filename strings, or
    positional tuples; every item is normalised to a :class:`FileEntry` via
    :meth:`FileEntry.from_raw` before ordering. Since only the name is used,
    no metric flags are needed.

    Args:
        files: List of file items (``FileEntry``, tuple, or ``str``).

    Returns:
        Reordered list of :class:`FileEntry` with name-similar files adjacent.
    """
    if not files:
        return []
    entries = [FileEntry.from_raw(f) for f in files]
    if len(entries) < 2:
        return entries
    remaining = sorted(entries, key=lambda e: e.name.lower())
    ordered: list[FileEntry] = [remaining.pop(0)]
    matcher = SequenceMatcher(autojunk=False)
    while remaining:
        matcher.set_seq2(ordered[-1].name.lower())
        best_idx = 0
        best_ratio = -1.0
        for idx, candidate in enumerate(remaining):
            matcher.set_seq1(candidate.name.lower())
            ratio = matcher.ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = idx
        ordered.append(remaining.pop(best_idx))
    return ordered


def sort_files_by_type(
    files: Sequence[Any],
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
    sort_by_similarity: bool = False,
) -> list[FileEntry]:
    """Sort files by extension and then by name, or by LOC/size/mtime/similarity if requested.

    The sort precedence follows: LOC > size > mtime > similarity >
    extension/name. The numeric metrics are mutually combinable and take
    priority; name-similarity grouping replaces the default extension/name
    ordering when requested but is itself overridden by any active numeric
    sort (a value-based ordering is treated as the stronger intent, exactly
    as it already overrides the plain alphabetical fallback).

    Inputs may be :class:`FileEntry` instances, bare filename strings, or
    positional tuples; every item is normalised to a :class:`FileEntry` via
    :meth:`FileEntry.from_raw` before sorting.

    Args:
        files: List of file items (``FileEntry``, tuple, or ``str``).
        sort_by_loc: Whether to sort by lines of code.
        sort_by_size: Whether to sort by file size.
        sort_by_mtime: Whether to sort by modification time.
        sort_by_similarity: Whether to group files by name similarity (used
            only when no numeric sort is active).

    Returns:
        Sorted list of :class:`FileEntry`.
    """
    if not files:
        return []

    has_loc = any(isinstance(item, tuple) and len(item) > 2 for item in files)
    has_size = any(isinstance(item, tuple) and len(item) > 3 for item in files)
    has_mtime = any(isinstance(item, tuple) and len(item) > 4 for item in files)
    has_simple_size = sort_by_size and not sort_by_loc and has_loc
    has_simple_mtime = (
        sort_by_mtime and not sort_by_loc and not sort_by_size and (has_loc or has_size)
    )

    entries = [
        FileEntry.from_raw(f, sort_by_loc, sort_by_size, sort_by_mtime) for f in files
    ]

    if sort_by_loc and sort_by_size and sort_by_mtime and has_mtime:
        return sorted(entries, key=lambda e: (-e.loc, -e.size, -e.mtime))
    if sort_by_loc and sort_by_size and (has_size or has_simple_size) and has_loc:
        return sorted(entries, key=lambda e: (-e.loc, -e.size))
    if sort_by_loc and sort_by_mtime and has_mtime:
        return sorted(entries, key=lambda e: (-e.loc, -e.mtime))
    if sort_by_size and sort_by_mtime and has_mtime:
        return sorted(entries, key=lambda e: (-e.size, -e.mtime))
    if sort_by_loc and has_loc:
        return sorted(entries, key=lambda e: -e.loc)
    if sort_by_size and (has_size or has_simple_size):
        return sorted(entries, key=lambda e: -e.size)
    if sort_by_mtime and (has_mtime or has_simple_mtime):
        return sorted(entries, key=lambda e: -e.mtime)
    if sort_by_similarity:
        return sort_files_by_similarity(entries)
    return sorted(
        entries,
        key=lambda e: (os.path.splitext(e.name)[1].lower(), e.name.lower()),
    )


RESERVED_KEYS: frozenset[str] = frozenset(
    {"_files", "_loc", "_size", "_mtime", "_max_depth_reached", "_git_markers"}
)


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


def format_dir_metrics(
    content: Any,
    *,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> str:
    """Return the space-prefixed metrics suffix for a directory node.

    Wraps :func:`format_metrics_suffix`, reading the totals from a directory's
    structure dict and enabling each metric only when it is both requested and
    present on that directory. Returns ``""`` for a non-dict node.

    Args:
        content: The directory's structure dict (or any value; non-dicts yield
            an empty string).
        sort_by_loc: Whether LOC display is requested.
        sort_by_size: Whether size display is requested.
        sort_by_mtime: Whether modification-time display is requested.

    Returns:
        The metrics suffix (with a leading space) or an empty string.
    """
    if not isinstance(content, dict):
        return ""
    return format_metrics_suffix(
        content.get("_loc", 0),
        content.get("_size", 0),
        content.get("_mtime", 0.0),
        sort_by_loc=sort_by_loc and "_loc" in content,
        sort_by_size=sort_by_size and "_size" in content,
        sort_by_mtime=sort_by_mtime and "_mtime" in content,
    )


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
    """Build the tree structure with colored file names.

    Recursively builds a rich.Tree representation of the directory structure with files color-coded by extension.

    When sort_by_loc is True, displays lines of code counts for files and directories.
    When sort_by_size is True, displays file sizes for files and directories.
    When sort_by_mtime is True, displays file modification times.
    When sort_by_similarity is True, groups files with similar names together
    (only applies when no numeric sort is active; it carries no annotation).
    When show_git_status is True, appends a coloured Git status marker to each file:
    ``[U]`` untracked (grey), ``[M]`` modified (yellow), ``[A]`` added (green),
    ``[D]`` deleted (red). Deleted files that no longer exist on disk are shown
    with a strikethrough style.

    Args:
        structure: Dictionary representation of the directory structure
        tree: Rich Tree object to build upon
        color_map: Mapping of file extensions to colors
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to display lines of code counts
        sort_by_size: Whether to display file sizes
        sort_by_mtime: Whether to display file modification times
        show_git_status: Whether to display Git status markers
        sort_by_similarity: Whether to group files by name similarity
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
    """Display a directory tree in the terminal with rich formatting.

    Presents a directory structure as a tree with:
    - Color-coded file extensions
    - Optional statistics (lines of code, sizes, modification times)
    - Optional grouping of similarly named files
    - Filtered content based on exclusion patterns
    - Depth limitations if specified
    - Optional Git status markers (when show_git_status is True)

    This function handles the entire process from scanning the directory to displaying the final tree visualization.

    Args:
        root_dir: Root directory path to display
        exclude_dirs: List of directory names to exclude
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude
        exclude_patterns: List of patterns to exclude
        include_patterns: List of patterns to include (overrides exclusions)
        use_regex: Whether to treat patterns as regex instead of glob patterns
        max_depth: Maximum depth to display (0 for unlimited)
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to show and sort by lines of code
        sort_by_size: Whether to show and sort by file size
        sort_by_mtime: Whether to show and sort by modification time
        show_git_status: Whether to annotate files with Git status markers
        icon_style: Style for displaying icons ("emoji" or "nerd")
        sort_by_similarity: Whether to group files by name similarity
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


def count_lines_of_code(file_path: str) -> int:
    """Count the number of lines in a file.

    Counts lines in text files while handling encoding issues and skipping binary files.
    Properly distinguishes between binary files with null bytes and UTF-16 encoded text files.

    Args:
        file_path: Path to the file

    Returns:
        Number of lines in the file, or 0 if the file cannot be read or is binary
    """
    try:
        with open(file_path, "rb") as binary_file:
            sample = binary_file.read(4096)
            if not sample:
                return 0
            utf16_le_bom = sample.startswith(b"\xff\xfe")
            utf16_be_bom = sample.startswith(b"\xfe\xff")
            if utf16_le_bom or utf16_be_bom:
                encoding = "utf-16-le" if utf16_le_bom else "utf-16-be"
                with open(file_path, encoding=encoding, errors="replace") as text_file:
                    return sum(1 for _ in text_file)
            potential_utf16le: bool = False
            potential_utf16be: bool = False
            if len(sample) >= 16:
                potential_utf16le = all(
                    sample[i] == 0 for i in range(1, min(32, len(sample)), 2)
                )
                potential_utf16be = all(
                    sample[i] == 0 for i in range(0, min(32, len(sample)), 2)
                )
                if potential_utf16le or potential_utf16be:
                    encoding = "utf-16-le" if potential_utf16le else "utf-16-be"
                    try:
                        with open(
                            file_path, encoding=encoding, errors="replace"
                        ) as text_file:
                            return sum(1 for _ in text_file)
                    except Exception:
                        pass
            if b"\x00" in sample and not (potential_utf16le or potential_utf16be):
                return 0
    except Exception as e:
        logger.debug(f"Could not analyze file: {file_path}: {e}")
        return 0
    try:
        with open(file_path, encoding="utf-8", errors="strict") as text_file:
            return sum(1 for _ in text_file)
    except UnicodeDecodeError:
        try:
            with open(file_path, encoding="utf-16", errors="strict") as text_file:
                return sum(1 for _ in text_file)
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"Could not read file as UTF-8: {file_path}: {e}")
        return 0
    try:
        with open(file_path, encoding="utf-8", errors="replace") as text_file:
            return sum(1 for _ in text_file)
    except Exception as e:
        logger.debug(f"Could not analyze file with replacement: {file_path}: {e}")
        return 0


def get_file_size(file_path: str) -> int:
    """Return the size of a file in bytes.

    Args:
        file_path: Path to the file whose size should be retrieved.

    Returns:
        Size of the file in bytes, or ``0`` when the file cannot be
        accessed (e.g., permission error or the path no longer exists).
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.debug(f"Could not get size for {file_path}: {e}")
        return 0


def format_size(size_in_bytes: int) -> str:
    """Format a size in bytes to a human-readable string.

    Converts raw byte counts to appropriate units (B, KB, MB, GB) with consistent formatting.

    Args:
        size_in_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "4.2 MB")
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_file_mtime(file_path: str) -> float:
    """Get the modification time of a file in seconds since epoch.

    Args:
        file_path: Path to the file

    Returns:
        Modification time as a float (seconds since epoch), or 0 if the file cannot be accessed
    """
    try:
        return os.path.getmtime(file_path)
    except Exception as e:
        logger.debug(f"Could not get modification time for {file_path}: {e}")
        return 0.0


def format_timestamp(timestamp: float) -> str:
    """Format a Unix timestamp to a human-readable string.

    Intelligently formats timestamps with different representations based on recency:
    - Today: "Today HH:MM"
    - Yesterday: "Yesterday HH:MM"
    - Last week: "Day HH:MM" (e.g., "Mon 14:30")
    - This year: "Month Day" (e.g., "Mar 15")
    - Older: "YYYY-MM-DD"

    Args:
        timestamp: Unix timestamp (seconds since epoch)

    Returns:
        Human-readable date/time string
    """
    if not timestamp:
        return "-"
    try:
        dt_object = dt.fromtimestamp(timestamp)
    except (OSError, OverflowError, ValueError):
        return "-"
    current_dt = dt.now()
    current_date = current_dt.date()
    if dt_object.date() == current_date:
        return f"Today {dt_object.strftime('%H:%M')}"
    elif dt_object.date() == current_date - datetime.timedelta(days=1):
        return f"Yesterday {dt_object.strftime('%H:%M')}"
    elif current_date - dt_object.date() < datetime.timedelta(days=7):
        return dt_object.strftime("%a %H:%M")
    elif dt_object.year == current_dt.year:
        return dt_object.strftime("%b %d")
    else:
        return dt_object.strftime("%Y-%m-%d")


def format_metrics(
    loc: int = 0,
    size: int = 0,
    mtime: float = 0.0,
    *,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> str:
    """Build the parenthetical metrics annotation for a file or directory.

    Includes only the metrics whose flag is set, always in the fixed order
    LOC, size, mtime — e.g. ``"(120 lines, 4.2 KB, Today 14:30)"``.

    Args:
        loc: Lines-of-code count.
        size: Size in bytes.
        mtime: Modification time (seconds since epoch).
        sort_by_loc: Include the LOC count.
        sort_by_size: Include the formatted size.
        sort_by_mtime: Include the formatted timestamp.

    Returns:
        The annotation string including the surrounding parentheses, or an
        empty string when no metric flag is set.
    """
    parts: list[str] = []
    if sort_by_loc:
        parts.append(f"{loc} lines")
    if sort_by_size:
        parts.append(format_size(size))
    if sort_by_mtime:
        parts.append(format_timestamp(mtime))
    return f"({', '.join(parts)})" if parts else ""


def format_metrics_suffix(
    loc: int = 0,
    size: int = 0,
    mtime: float = 0.0,
    *,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> str:
    """Like :func:`format_metrics` but prefixed with a single space.

    Convenient for appending directly after a file or directory name. Returns
    an empty string (no leading space) when no metric flag is set.
    """
    metrics = format_metrics(
        loc,
        size,
        mtime,
        sort_by_loc=sort_by_loc,
        sort_by_size=sort_by_size,
        sort_by_mtime=sort_by_mtime,
    )
    return f" {metrics}" if metrics else ""
