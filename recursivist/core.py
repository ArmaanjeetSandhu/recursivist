import colorsys
import fnmatch
import hashlib
import logging
import os
from typing import Dict, List, Optional, Set, Tuple

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from recursivist.exports import DirectoryExporter

logger = logging.getLogger(__name__)


def export_structure(
    structure: Dict, root_dir: str, format_type: str, output_path: str
) -> None:
    """Export the directory structure to various formats.

    Args:
        structure: Directory structure dictionary
        root_dir: Root directory name
        format_type: Export format ('txt', 'json', 'html', 'md', 'jsx')
        output_path: Path where the export file will be saved

    Raises:
        ValueError: If the format_type is not supported
    """
    exporter = DirectoryExporter(structure, os.path.basename(root_dir))

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
    logger.info("Successfully exported to %s", output_path)


def parse_ignore_file(ignore_file_path: str) -> List[str]:
    """Parse an ignore file (like .gitignore) and return patterns.

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


def should_exclude(
    path: str, ignore_context: Dict, exclude_extensions: Optional[Set[str]] = None
) -> bool:
    """Check if a path should be excluded based on ignore patterns and extensions.

    Args:
        path: Path to check
        ignore_context: Dictionary with 'patterns' and 'current_dir' keys
        exclude_extensions: Set of file extensions to exclude

    Returns:
        True if path should be excluded
    """
    patterns = ignore_context.get("patterns", [])
    current_dir = ignore_context.get("current_dir", os.path.dirname(path))

    if exclude_extensions and os.path.isfile(path):
        _, ext = os.path.splitext(path)
        if ext.lower() in exclude_extensions:
            return True

    if not patterns:
        return False

    rel_path = os.path.relpath(path, current_dir)

    for pattern in patterns:
        if pattern.startswith("!"):
            if fnmatch.fnmatch(rel_path, pattern[1:]):
                return False
        elif fnmatch.fnmatch(rel_path, pattern):
            return True

    return False


def generate_color_for_extension(extension: str) -> str:
    """Generate a consistent color for a given file extension.

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
) -> Tuple[Dict, Set[str]]:
    """Build a nested dictionary representing the directory structure.

    Args:
        root_dir: Root directory path to start from
        exclude_dirs: List of directory names to exclude
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude
        parent_ignore_patterns: Patterns from parent directories

    Returns:
        Tuple of (structure dictionary, set of extensions found)
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_extensions is None:
        exclude_extensions = set()

    ignore_patterns = parent_ignore_patterns.copy() if parent_ignore_patterns else []

    if ignore_file and os.path.exists(os.path.join(root_dir, ignore_file)):
        current_ignore_patterns = parse_ignore_file(os.path.join(root_dir, ignore_file))
        ignore_patterns.extend(current_ignore_patterns)

    ignore_context = {"patterns": ignore_patterns, "current_dir": root_dir}

    structure = {}
    extensions_set = set()

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
            item_path, ignore_context, exclude_extensions
        ):
            continue

        if os.path.isdir(item_path):
            substructure, sub_extensions = get_directory_structure(
                item_path,
                exclude_dirs,
                ignore_file,
                exclude_extensions,
                ignore_patterns,
            )
            structure[item] = substructure
            extensions_set.update(sub_extensions)
        else:
            _, ext = os.path.splitext(item)
            if ext.lower() not in exclude_extensions:
                structure.setdefault("_files", []).append(item)
                if ext:
                    extensions_set.add(ext.lower())

    return structure, extensions_set


def sort_files_by_type(files: List[str]) -> List[str]:
    """Sort files by extension and then by name.

    Args:
        files: List of filenames to sort

    Returns:
        Sorted list of filenames
    """
    return sorted(files, key=lambda f: (os.path.splitext(f)[1], f.lower()))


def build_tree(
    structure: Dict, tree: Tree, color_map: Dict[str, str], parent_name: str = "Root"
) -> None:
    """Build the tree structure with colored file names.

    Args:
        structure: Dictionary representation of the directory structure
        tree: Rich Tree object to build upon
        color_map: Mapping of file extensions to colors
        parent_name: Name of the parent directory
    """
    for folder, content in sorted(structure.items()):
        if folder == "_files":
            for file in sort_files_by_type(content):
                ext = os.path.splitext(file)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                colored_text = Text(f"📄 {file}", style=color)
                tree.add(colored_text)
        else:
            subtree = tree.add(f"📁 {folder}")
            build_tree(content, subtree, color_map, folder)


def display_tree(
    root_dir: str,
    exclude_dirs: Optional[List[str]] = None,
    ignore_file: Optional[str] = None,
    exclude_extensions: Optional[Set[str]] = None,
) -> None:
    """Display the directory tree with color-coded file types.

    Args:
        root_dir: Root directory path to display
        exclude_dirs: List of directory names to exclude from the tree
        ignore_file: Name of ignore file (like .gitignore)
        exclude_extensions: Set of file extensions to exclude (e.g., {'.pyc', '.log'})
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_extensions is None:
        exclude_extensions = set()

    exclude_extensions = {
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in exclude_extensions
    }

    structure, extensions = get_directory_structure(
        root_dir, exclude_dirs, ignore_file, exclude_extensions
    )

    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}

    console = Console()
    tree = Tree(f"📂 {os.path.basename(root_dir)}")
    build_tree(structure, tree, color_map)
    console.print(tree)
