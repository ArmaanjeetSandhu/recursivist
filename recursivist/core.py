"""
Core functionality for the Recursivist directory visualization tool.

This module provides the fundamental components for building, filtering, displaying, and exporting directory structures. It handles directory traversal, pattern matching, color coding, and tree construction for visual representation.

Key features include:
- Directory structure parsing and representation
- Flexible pattern-based filtering (glob/regex)
- Customizable depth limits and path displays
- Color-coding by file extension
- Support for ignore files (like .gitignore)
- Tree visualization with rich formatting
"""

import colorsys
import fnmatch
import hashlib
import logging
import os
import re
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union, cast

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from recursivist.exports import DirectoryExporter

logger = logging.getLogger(__name__)


def export_structure(
    structure: Dict,
    root_dir: str,
    format_type: str,
    output_path: str,
    show_full_path: bool = False,
) -> None:
    """Export the directory structure to various formats.

    Maps the requested format to the appropriate export method using DirectoryExporter. Handles txt, json, html, md, and jsx formats with consistent styling.

    Args:
        structure: Directory structure dictionary
        root_dir: Root directory name
        format_type: Export format ('txt', 'json', 'html', 'md', 'jsx')
        output_path: Path where the export file will be saved
        show_full_path: Whether to show full paths instead of just filenames

    Raises:
        ValueError: If the format_type is not supported
    """
    exporter = DirectoryExporter(
        structure, os.path.basename(root_dir), root_dir if show_full_path else None
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
    with open(ignore_file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if line.endswith("/"):
                    line = line[:-1]
                patterns.append(line)
    return patterns


def compile_regex_patterns(
    patterns: List[str], is_regex: bool = False
) -> List[Union[str, Pattern[str]]]:
    """Compile regex patterns if needed.

    Converts string patterns to compiled regex patterns when is_regex is True. For invalid regex patterns, logs a warning and keeps them as strings.

    Args:
        patterns: List of patterns to compile
        is_regex: Whether the patterns should be treated as regex or glob patterns

    Returns:
        List of patterns (either strings for glob patterns or compiled regex patterns)
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
    ignore_context: Dict,
    exclude_extensions: Optional[Set[str]] = None,
    exclude_patterns: Optional[List[Union[str, Pattern[str]]]] = None,
    include_patterns: Optional[List[Union[str, Pattern[str]]]] = None,
) -> bool:
    """Check if a path should be excluded based on ignore patterns, extensions, and regex patterns.

    Decision hierarchy:
    1. If include_patterns match, INCLUDE the path (overrides all exclusions)
    2. If exclude_patterns match, EXCLUDE the path
    3. If file extension is in exclude_extensions, EXCLUDE the path
    4. If gitignore-style patterns match, use their rules

    Args:
        path: Path to check
        ignore_context: Dictionary with 'patterns' and 'current_dir' keys
        exclude_extensions: Set of file extensions to exclude
        exclude_patterns: List of regex patterns to exclude
        include_patterns: List of regex patterns to include (overrides exclusions)

    Returns:
        True if path should be excluded
    """
    patterns = ignore_context.get("patterns", [])
    current_dir = ignore_context.get("current_dir", os.path.dirname(path))
    if exclude_extensions and os.path.isfile(path):
        _, ext = os.path.splitext(path)
        if ext.lower() in exclude_extensions:
            return True
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
        if included:
            return False
        else:
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
    if not patterns:
        return False
    for pattern in patterns:
        if isinstance(pattern, str):
            if pattern.startswith("!"):
                if fnmatch.fnmatch(rel_path, pattern[1:]):
                    return False
            elif fnmatch.fnmatch(rel_path, pattern):
                return True
    return False


def generate_color_for_extension(extension: str) -> str:
    """Generate a consistent color for a given file extension.

    Uses a hash function to derive a consistent color for each extension, ensuring the same extension always gets the same color within a session. Colors are in the HSV color space with fixed saturation and value but varying hue based on the hash.

    Args:
        extension: File extension (with or without leading dot)

    Returns:
        Hex color code
    """
    if not extension:
        return "#FFFFFF"
    hash_value = int(hashlib.md5(extension.encode()).hexdigest(), 16)
    hue = hash_value % 360 / 360.0
    saturation = 0.7
    value = 0.95
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    return "#{:02x}{:02x}{:02x}".format(
        int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
    )


def get_directory_structure(
    root_dir: str,
    exclude_dirs: Optional[List[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[Set[str]] = None,
    parent_ignore_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[Union[str, Pattern[str]]]] = None,
    include_patterns: Optional[List[Union[str, Pattern[str]]]] = None,
    max_depth: int = 0,
    current_depth: int = 0,
    current_path: str = "",
    show_full_path: bool = False,
) -> Tuple[Dict[str, Any], Set[str]]:
    """Build a nested dictionary representing the directory structure.

    Recursively traverses the file system starting at root_dir, applying filters and building a structured representation. For files, handles both simple filenames and (filename, full_path) tuples based on show_full_path setting.

    The returned dictionary has the following structure:
    - Keys are directory names
    - Values are either subdirectory dictionaries or special keys:
      - '_files': List of files (either strings or tuples with full paths)
      - '_max_depth_reached': Boolean flag when max_depth is reached

    Args:
        root_dir: Root directory path to start from
        exclude_dirs: List of directory names to exclude
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude
        parent_ignore_patterns: Patterns from parent directories
        exclude_patterns: List of regex patterns to exclude
        include_patterns: List of regex patterns to include (overrides exclusions)
        max_depth: Maximum depth to traverse (0 for unlimited)
        current_depth: Current depth in the directory tree
        current_path: Current path for full path display
        show_full_path: Whether to show full paths instead of just filenames

    Returns:
        Tuple of (structure dictionary, set of extensions found)
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_extensions is None:
        exclude_extensions = set()
    if exclude_patterns is None:
        exclude_patterns = []
    if include_patterns is None:
        include_patterns = []
    ignore_patterns = parent_ignore_patterns.copy() if parent_ignore_patterns else []
    if ignore_file and os.path.exists(os.path.join(root_dir, ignore_file)):
        current_ignore_patterns = parse_ignore_file(os.path.join(root_dir, ignore_file))
        ignore_patterns.extend(current_ignore_patterns)
    ignore_context = {"patterns": ignore_patterns, "current_dir": root_dir}
    structure: Dict[str, Any] = {}
    extensions_set: Set[str] = set()
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
                if show_full_path:
                    abs_path = os.path.abspath(item_path)
                    abs_path = abs_path.replace(os.sep, "/")
                    structure["_files"].append((item, abs_path))
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
            )
            structure[item] = substructure
            extensions_set.update(sub_extensions)
    return structure, extensions_set


def sort_files_by_type(
    files: List[Union[str, Tuple[str, str]]],
) -> List[Union[str, Tuple[str, str]]]:
    """Sort files by extension and then by name.

    Handles mixed input of both strings and tuples, ensuring correct sorting in either case. The extension is the primary sort key, followed by the filename as a secondary key.

    Args:
        files: List of filenames or (filename, full_path) tuples to sort

    Returns:
        Sorted list of filenames or tuples
    """
    if not files:
        return []
    all_tuples = all(isinstance(item, tuple) for item in files)
    all_strings = all(isinstance(item, str) for item in files)
    if all_strings:
        files_as_strings = cast(List[str], files)
        return cast(
            List[Union[str, Tuple[str, str]]],
            sorted(
                files_as_strings,
                key=lambda f: (os.path.splitext(f)[1].lower(), f.lower()),
            ),
        )
    elif all_tuples:
        files_as_tuples = cast(List[Tuple[str, str]], files)
        return cast(
            List[Union[str, Tuple[str, str]]],
            sorted(
                files_as_tuples,
                key=lambda t: (os.path.splitext(t[0])[1].lower(), t[0].lower()),
            ),
        )
    else:
        str_items: List[str] = []
        tuple_items: List[Tuple[str, str]] = []
        for item in files:
            if isinstance(item, tuple):
                tuple_items.append(cast(Tuple[str, str], item))
            else:
                str_items.append(cast(str, item))
        sorted_strings = sorted(
            str_items, key=lambda f: (os.path.splitext(f)[1].lower(), f.lower())
        )
        sorted_tuples = sorted(
            tuple_items, key=lambda t: (os.path.splitext(t[0])[1].lower(), t[0].lower())
        )
        result: List[Union[str, Tuple[str, str]]] = []
        for item in sorted_strings:
            result.append(item)
        for item in sorted_tuples:
            result.append(item)
        return result


def build_tree(
    structure: Dict,
    tree: Tree,
    color_map: Dict[str, str],
    parent_name: str = "Root",
    show_full_path: bool = False,
) -> None:
    """Build the tree structure with colored file names.

    Recursively builds a rich.Tree representation of the directory structure with files color-coded by extension. Handles both simple filenames and full paths based on show_full_path setting.

    Args:
        structure: Dictionary representation of the directory structure
        tree: Rich Tree object to build upon
        color_map: Mapping of file extensions to colors
        parent_name: Name of the parent directory
        show_full_path: Whether to show full paths instead of just filenames
    """
    for folder, content in sorted(structure.items()):
        if folder == "_files":
            for file_item in sort_files_by_type(content):
                if show_full_path and isinstance(file_item, tuple):
                    file_name, full_path = file_item
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(f"📄 {full_path}", style=color)
                    tree.add(colored_text)
                else:
                    if isinstance(file_item, tuple):
                        file_name, _ = file_item
                    else:
                        file_name = cast(str, file_item)
                    ext = os.path.splitext(file_name)[1].lower()
                    color = color_map.get(ext, "#FFFFFF")
                    colored_text = Text(f"📄 {file_name}", style=color)
                    tree.add(colored_text)
        elif folder == "_max_depth_reached":
            pass
        else:
            subtree = tree.add(f"📁 {folder}")
            if isinstance(content, dict) and content.get("_max_depth_reached"):
                subtree.add(Text("⋯ (max depth reached)", style="dim"))
            else:
                build_tree(content, subtree, color_map, folder, show_full_path)


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
) -> None:
    """Display the directory tree with color-coded file types.

    Prepares the directory structure with all filtering options applied, then builds and displays a Rich tree visualization with color-coding based on file extensions.

    Args:
        root_dir: Root directory path to display
        exclude_dirs: List of directory names to exclude from the tree
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude (e.g., {'.pyc', '.log'})
        exclude_patterns: List of patterns to exclude
        include_patterns: List of patterns to include (overrides exclusions)
        use_regex: Whether to treat patterns as regex instead of glob patterns
        max_depth: Maximum depth to display (0 for unlimited)
        show_full_path: Whether to show full paths instead of just filenames
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
        root_dir,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        exclude_patterns=compiled_exclude,
        include_patterns=compiled_include,
        max_depth=max_depth,
        show_full_path=show_full_path,
    )
    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}
    console = Console()
    tree = Tree(f"📂 {os.path.basename(root_dir)}")
    build_tree(structure, tree, color_map, show_full_path=show_full_path)
    console.print(tree)
