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
from datetime import datetime as dt
from typing import Any, Dict, List, Optional, Pattern, Sequence, Set, Tuple, Union, cast

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

logger = logging.getLogger(__name__)


def export_structure(
    structure: Dict[str, Any],
    root_dir: str,
    format_type: str,
    output_path: str,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> None:
    """Export the directory structure to various formats.

    Maps the requested format to the appropriate export method using DirectoryExporter. Handles txt, json, html, md, and jsx formats with consistent styling.

    Args:
        structure: Directory structure dictionary
        root_dir: Root directory name
        format_type: Export format ('txt', 'json', 'html', 'md', 'jsx')
        output_path: Path where the export file will be saved
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to include lines of code counts in the export
        sort_by_size: Whether to include file size information in the export
        sort_by_mtime: Whether to include file modification times in the export

    Raises:
        ValueError: If the format_type is not supported
    """
    from recursivist.exports import DirectoryExporter

    exporter = DirectoryExporter(
        structure,
        os.path.basename(root_dir),
        root_dir if show_full_path else None,
        sort_by_loc,
        sort_by_size,
        sort_by_mtime,
    )
    format_map = {
        "txt": exporter.to_txt,
        "json": exporter.to_json,
        "html": exporter.to_html,
        "md": exporter.to_markdown,
        "jsx": exporter.to_jsx,
    }
    if format_type.lower() not in format_map:
        raise ValueError(f"Unsupported format: {format_type}")
    export_func = format_map[format_type.lower()]
    export_func(output_path)


def parse_ignore_file(ignore_file_path: str) -> List[str]:
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
                if line.endswith("/"):
                    line = line[:-1]
                patterns.append(line)
    return patterns


def compile_regex_patterns(
    patterns: Sequence[str], is_regex: bool = False
) -> List[Union[str, Pattern[str]]]:
    """Convert patterns to compiled regex objects when appropriate.

    When is_regex is True, compiles string patterns into regex pattern objects for efficient matching. For invalid regex patterns, logs a warning and keeps them as strings.

    Args:
        patterns: List of patterns to compile
        is_regex: Whether the patterns should be treated as regex (True) or glob patterns (False)

    Returns:
        List of patterns (strings for glob patterns or compiled regex objects)
    """
    if not is_regex:
        return cast(List[Union[str, Pattern[str]]], patterns)
    compiled_patterns: List[Union[str, Pattern[str]]] = []
    for pattern in patterns:
        try:
            compiled_patterns.append(re.compile(pattern))
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            compiled_patterns.append(pattern)
    return compiled_patterns


def should_exclude(
    path: str,
    ignore_context: Dict[str, Any],
    exclude_extensions: Optional[Set[str]] = None,
    exclude_patterns: Optional[Sequence[Union[str, Pattern[str]]]] = None,
    include_patterns: Optional[Sequence[Union[str, Pattern[str]]]] = None,
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
    if include_patterns:
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
    for pattern in patterns:
        if isinstance(pattern, str) and pattern.startswith("!"):
            if fnmatch.fnmatch(rel_path, pattern[1:]):
                return False
    for pattern in patterns:
        if isinstance(pattern, str) and not pattern.startswith("!"):
            if fnmatch.fnmatch(rel_path, pattern):
                return True
    return False


_EXTENSION_COLORS: Dict[str, str] = {}


def color_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """
    Calculate perceptual distance between two colors in RGB space.

    Using a weighted Euclidean distance that accounts for human perception.

    Args:
        color1: First color as (r, g, b) tuple with values 0-255
        color2: Second color as (r, g, b) tuple with values 0-255

    Returns:
        Float representing perceptual distance
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


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return cast(
        Tuple[int, int, int], tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    )


def generate_color_for_extension(extension: str) -> str:
    """Generate a consistent color for a file extension with collision detection.

    Creates a deterministic color based on the extension string using a hash function.  The same extension will always get the same color within a session, and different extensions get visually distinct colors.

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
    hash_bytes = hashlib.md5(normalized_ext.encode()).digest()
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
    best_min_distance = 0
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
            best_min_distance = int(min_distance)
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
    exclude_dirs: Optional[Sequence[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[Set[str]] = None,
    parent_ignore_patterns: Optional[Sequence[str]] = None,
    exclude_patterns: Optional[Sequence[Union[str, Pattern[str]]]] = None,
    include_patterns: Optional[Sequence[Union[str, Pattern[str]]]] = None,
    max_depth: int = 0,
    current_depth: int = 0,
    current_path: str = "",
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> Tuple[Dict[str, Any], Set[str]]:
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
    ignore_context = {"patterns": ignore_patterns, "current_dir": root_dir}
    structure: Dict[str, Any] = {}
    extensions_set: Set[str] = set()
    total_loc = 0
    total_size = 0
    latest_mtime = 0.0
    if max_depth > 0 and current_depth >= max_depth:
        return {"_max_depth_reached": True}, extensions_set
    try:
        items = os.listdir(root_dir)
    except PermissionError:
        logger.warning(f"Permission denied: {root_dir}")
        return structure, extensions_set
    except Exception as e:
        logger.error(f"Error reading directory {root_dir}: {e}")
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
                    abs_path = os.path.abspath(item_path)
                    abs_path = abs_path.replace(os.sep, "/")
                    if sort_by_loc and sort_by_size and sort_by_mtime:
                        structure["_files"].append(
                            (item, abs_path, file_loc, file_size, file_mtime)
                        )
                    elif sort_by_loc and sort_by_size:
                        structure["_files"].append(
                            (item, abs_path, file_loc, file_size)
                        )
                    elif sort_by_loc and sort_by_mtime:
                        structure["_files"].append(
                            (item, abs_path, file_loc, 0, file_mtime)
                        )
                    elif sort_by_size and sort_by_mtime:
                        structure["_files"].append(
                            (item, abs_path, 0, file_size, file_mtime)
                        )
                    elif sort_by_loc:
                        structure["_files"].append((item, abs_path, file_loc))
                    elif sort_by_size:
                        structure["_files"].append((item, abs_path, file_size))
                    elif sort_by_mtime:
                        structure["_files"].append((item, abs_path, file_mtime))
                    else:
                        structure["_files"].append((item, abs_path))
                else:
                    if sort_by_loc and sort_by_size and sort_by_mtime:
                        structure["_files"].append(
                            (item, item, file_loc, file_size, file_mtime)
                        )
                    elif sort_by_loc and sort_by_size:
                        structure["_files"].append((item, item, file_loc, file_size))
                    elif sort_by_loc and sort_by_mtime:
                        structure["_files"].append(
                            (item, item, file_loc, 0, file_mtime)
                        )
                    elif sort_by_size and sort_by_mtime:
                        structure["_files"].append(
                            (item, item, 0, file_size, file_mtime)
                        )
                    elif sort_by_loc:
                        structure["_files"].append((item, item, file_loc))
                    elif sort_by_size:
                        structure["_files"].append((item, item, file_size))
                    elif sort_by_mtime:
                        structure["_files"].append((item, item, file_mtime))
                    else:
                        structure["_files"].append(item)
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
            )
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
    return structure, extensions_set


def sort_files_by_type(
    files: Sequence[
        Union[
            str,
            Tuple[str, str],
            Tuple[str, str, int],
            Tuple[str, str, int, int],
            Tuple[str, str, int, int, float],
        ]
    ],
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> List[
    Union[
        str,
        Tuple[str, str],
        Tuple[str, str, int],
        Tuple[str, str, int, int],
        Tuple[str, str, int, int, float],
    ]
]:
    """Sort files by extension and then by name, or by LOC/size/mtime if requested.

    The sort precedence follows: LOC > size > mtime > extension/name

    Args:
        files: List of file items, which can be strings or tuples of various forms
        sort_by_loc: Whether to sort by lines of code
        sort_by_size: Whether to sort by file size
        sort_by_mtime: Whether to sort by modification time

    Returns:
        Sorted list of file items
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

    def get_size(
        item: Union[
            str,
            Tuple[str, str],
            Tuple[str, str, int],
            Tuple[str, str, int, int],
            Tuple[str, str, int, int, float],
        ],
    ) -> int:
        if not isinstance(item, tuple):
            return 0
        if len(item) > 3:
            if sort_by_loc and sort_by_size:
                return item[3]
            elif sort_by_size and not sort_by_loc:
                return item[3]
        elif len(item) == 3 and sort_by_size:
            return item[2]
        return 0

    def get_loc(
        item: Union[
            str,
            Tuple[str, str],
            Tuple[str, str, int],
            Tuple[str, str, int, int],
            Tuple[str, str, int, int, float],
        ],
    ) -> int:
        if not isinstance(item, tuple) or len(item) <= 2:
            return 0
        return item[2] if sort_by_loc else 0

    def get_mtime(
        item: Union[
            str,
            Tuple[str, str],
            Tuple[str, str, int],
            Tuple[str, str, int, int],
            Tuple[str, str, int, int, float],
        ],
    ) -> float:
        if not isinstance(item, tuple):
            return 0
        if len(item) > 4:
            return item[4]
        elif len(item) > 3 and (
            (sort_by_loc and sort_by_mtime and not sort_by_size)
            or (sort_by_size and sort_by_mtime and not sort_by_loc)
        ):
            return item[3]
        elif len(item) > 2 and sort_by_mtime and not sort_by_loc and not sort_by_size:
            return item[2]
        return 0

    if sort_by_loc and sort_by_size and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_loc(f), -get_size(f), -get_mtime(f)))
    elif sort_by_loc and sort_by_size and (has_size or has_simple_size) and has_loc:
        return sorted(files, key=lambda f: (-get_loc(f), -get_size(f)))
    elif sort_by_loc and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_loc(f), -get_mtime(f)))
    elif sort_by_size and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_size(f), -get_mtime(f)))
    elif sort_by_loc and has_loc:
        return sorted(files, key=lambda f: -get_loc(f))
    elif sort_by_size and (has_size or has_simple_size):
        return sorted(files, key=lambda f: -get_size(f))
    elif sort_by_mtime and (has_mtime or has_simple_mtime):
        return sorted(files, key=lambda f: -get_mtime(f))

    def get_filename(
        item: Union[
            str,
            Tuple[str, str],
            Tuple[str, str, int],
            Tuple[str, str, int, int],
            Tuple[str, str, int, int, float],
        ],
    ) -> str:
        if isinstance(item, tuple):
            return item[0]
        return item

    return sorted(
        files,
        key=lambda f: (
            os.path.splitext(get_filename(f))[1].lower(),
            get_filename(f).lower(),
        ),
    )


def build_tree(
    structure: Dict[str, Any],
    tree: Tree,
    color_map: Dict[str, str],
    parent_name: str = "Root",
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> None:
    """Build the tree structure with colored file names.

    Recursively builds a rich.Tree representation of the directory structure with files color-coded by extension.

    When sort_by_loc is True, displays lines of code counts for files and directories.
    When sort_by_size is True, displays file sizes for files and directories.
    When sort_by_mtime is True, displays file modification times.

    Args:
        structure: Dictionary representation of the directory structure
        tree: Rich Tree object to build upon
        color_map: Mapping of file extensions to colors
        parent_name: Name of the parent directory
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to display lines of code counts
        sort_by_size: Whether to display file sizes
        sort_by_mtime: Whether to display file modification times
    """
    for folder, content in sorted(structure.items()):
        if folder == "_files":
            for file_item in sort_files_by_type(
                content, sort_by_loc, sort_by_size, sort_by_mtime
            ):
                file_name = ""
                full_path = ""
                loc = 0
                size = 0
                mtime = 0.0
                if isinstance(file_item, tuple):
                    file_name = file_item[0]
                    if len(file_item) > 1:
                        full_path = file_item[1]
                    else:
                        full_path = file_name
                    if len(file_item) > 2:
                        if (
                            sort_by_loc
                            and sort_by_size
                            and sort_by_mtime
                            and len(file_item) > 4
                        ):
                            loc = file_item[2]
                            size = file_item[3]
                            mtime = file_item[4]
                        elif sort_by_loc and sort_by_size and len(file_item) > 3:
                            loc = file_item[2]
                            size = file_item[3]
                        elif sort_by_loc and sort_by_mtime and len(file_item) > 4:
                            loc = file_item[2]
                            mtime = file_item[4]
                        elif sort_by_size and sort_by_mtime and len(file_item) > 4:
                            size = file_item[3]
                            mtime = file_item[4]
                        elif sort_by_loc and len(file_item) > 2:
                            loc = file_item[2]
                        elif sort_by_size and len(file_item) > 2:
                            size = file_item[2]
                        elif sort_by_mtime and len(file_item) > 2:
                            mtime = file_item[2]
                else:
                    file_name = file_item
                    full_path = file_name
                display_path = full_path if show_full_path else file_name
                ext = os.path.splitext(file_name)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                if sort_by_loc and sort_by_size and sort_by_mtime and loc > 0:
                    colored_text = Text(
                        f"📄 {display_path} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})",
                        style=color,
                    )
                elif sort_by_loc and sort_by_mtime and loc > 0:
                    colored_text = Text(
                        f"📄 {display_path} ({loc} lines, {format_timestamp(mtime)})",
                        style=color,
                    )
                elif sort_by_size and sort_by_mtime and size > 0:
                    colored_text = Text(
                        f"📄 {display_path} ({format_size(size)}, {format_timestamp(mtime)})",
                        style=color,
                    )
                elif sort_by_loc and sort_by_size and loc > 0:
                    colored_text = Text(
                        f"📄 {display_path} ({loc} lines, {format_size(size)})",
                        style=color,
                    )
                elif sort_by_loc and loc > 0:
                    colored_text = Text(
                        f"📄 {display_path} ({loc} lines)",
                        style=color,
                    )
                elif sort_by_size and size > 0:
                    colored_text = Text(
                        f"📄 {display_path} ({format_size(size)})",
                        style=color,
                    )
                elif sort_by_mtime and mtime > 0:
                    colored_text = Text(
                        f"📄 {display_path} ({format_timestamp(mtime)})",
                        style=color,
                    )
                else:
                    colored_text = Text(f"📄 {display_path}", style=color)
                tree.add(colored_text)
        elif (
            folder == "_loc"
            or folder == "_size"
            or folder == "_mtime"
            or folder == "_max_depth_reached"
        ):
            pass
        else:
            folder_display = f"📁 {folder}"
            if (
                sort_by_loc
                and sort_by_size
                and sort_by_mtime
                and isinstance(content, dict)
            ):
                if "_loc" in content and "_size" in content and "_mtime" in content:
                    folder_loc = content["_loc"]
                    folder_size = content["_size"]
                    folder_mtime = content["_mtime"]
                    folder_display = f"📁 {folder} ({folder_loc} lines, {format_size(folder_size)}, {format_timestamp(folder_mtime)})"
            elif sort_by_loc and sort_by_size and isinstance(content, dict):
                if "_loc" in content and "_size" in content:
                    folder_loc = content["_loc"]
                    folder_size = content["_size"]
                    folder_display = (
                        f"📁 {folder} ({folder_loc} lines, {format_size(folder_size)})"
                    )
            elif sort_by_loc and sort_by_mtime and isinstance(content, dict):
                if "_loc" in content and "_mtime" in content:
                    folder_loc = content["_loc"]
                    folder_mtime = content["_mtime"]
                    folder_display = f"📁 {folder} ({folder_loc} lines, {format_timestamp(folder_mtime)})"
            elif sort_by_size and sort_by_mtime and isinstance(content, dict):
                if "_size" in content and "_mtime" in content:
                    folder_size = content["_size"]
                    folder_mtime = content["_mtime"]
                    folder_display = f"📁 {folder} ({format_size(folder_size)}, {format_timestamp(folder_mtime)})"
            elif sort_by_loc and isinstance(content, dict) and "_loc" in content:
                folder_loc = content["_loc"]
                folder_display = f"📁 {folder} ({folder_loc} lines)"
            elif sort_by_size and isinstance(content, dict) and "_size" in content:
                folder_size = content["_size"]
                folder_display = f"📁 {folder} ({format_size(folder_size)})"
            elif sort_by_mtime and isinstance(content, dict) and "_mtime" in content:
                folder_mtime = content["_mtime"]
                folder_display = f"📁 {folder} ({format_timestamp(folder_mtime)})"
            subtree = tree.add(folder_display)
            if isinstance(content, dict) and content.get("_max_depth_reached"):
                subtree.add(Text("⋯ (max depth reached)", style="dim"))
            else:
                build_tree(
                    content,
                    subtree,
                    color_map,
                    folder,
                    show_full_path,
                    sort_by_loc,
                    sort_by_size,
                    sort_by_mtime,
                )


def display_tree(
    root_dir: str,
    exclude_dirs: Optional[List[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[Set[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    use_regex: bool = False,
    max_depth: int = 0,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> None:
    """Display a directory tree in the terminal with rich formatting.

    Presents a directory structure as a tree with:
    - Color-coded file extensions
    - Optional statistics (lines of code, sizes, modification times)
    - Filtered content based on exclusion patterns
    - Depth limitations if specified

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
    )
    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}
    console = Console()
    root_label = f"📂 {os.path.basename(root_dir)}"
    if (
        sort_by_loc
        and sort_by_size
        and sort_by_mtime
        and "_loc" in structure
        and "_size" in structure
        and "_mtime" in structure
    ):
        root_label = f"📂 {os.path.basename(root_dir)} ({structure['_loc']} lines, {format_size(structure['_size'])}, {format_timestamp(structure['_mtime'])})"
    elif sort_by_loc and sort_by_size and "_loc" in structure and "_size" in structure:
        root_label = f"📂 {os.path.basename(root_dir)} ({structure['_loc']} lines, {format_size(structure['_size'])})"
    elif (
        sort_by_loc and sort_by_mtime and "_loc" in structure and "_mtime" in structure
    ):
        root_label = f"📂 {os.path.basename(root_dir)} ({structure['_loc']} lines, {format_timestamp(structure['_mtime'])})"
    elif (
        sort_by_size
        and sort_by_mtime
        and "_size" in structure
        and "_mtime" in structure
    ):
        root_label = f"📂 {os.path.basename(root_dir)} ({format_size(structure['_size'])}, {format_timestamp(structure['_mtime'])})"
    elif sort_by_loc and "_loc" in structure:
        root_label = f"📂 {os.path.basename(root_dir)} ({structure['_loc']} lines)"
    elif sort_by_size and "_size" in structure:
        root_label = (
            f"📂 {os.path.basename(root_dir)} ({format_size(structure['_size'])})"
        )
    elif sort_by_mtime and "_mtime" in structure:
        root_label = (
            f"📂 {os.path.basename(root_dir)} ({format_timestamp(structure['_mtime'])})"
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
    if file_path.lower().endswith(".bin"):
        return 0
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
    """Get the size of a file in bytes.
    Args:
        file_path: Path to the file
    Returns:
        Size of the file in bytes, or 0 if the file cannot be accessed
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
    dt_object = dt.fromtimestamp(timestamp)
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
