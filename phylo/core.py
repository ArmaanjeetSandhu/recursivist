import os
from rich.tree import Tree
from rich.console import Console
from rich.text import Text
import colorsys
import hashlib
import fnmatch
from pathlib import Path


def parse_ignore_file(ignore_file_path):
    """Parse an ignore file (like .gitignore) and return patterns.

    Args:
        ignore_file_path (str): Path to the ignore file

    Returns:
        list: List of parsed patterns
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


def should_exclude(path, patterns, root_dir):
    """Check if a path should be excluded based on ignore patterns.

    Args:
        path (str): Path to check
        patterns (list): List of ignore patterns
        root_dir (str): Root directory for relative path calculation

    Returns:
        bool: True if path should be excluded
    """
    if not patterns:
        return False

    rel_path = os.path.relpath(path, root_dir)

    for pattern in patterns:
        if pattern.startswith("!"):
            if fnmatch.fnmatch(rel_path, pattern[1:]):
                return False
        elif fnmatch.fnmatch(rel_path, pattern):
            return True

    return False


def generate_color_for_extension(extension):
    """Generate a consistent color for a given file extension."""
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


def get_directory_structure(root_dir, exclude_dirs=None, ignore_patterns=None):
    """Build a nested dictionary representing the directory structure.

    Args:
        root_dir (str): Root directory path to start from
        exclude_dirs (list): List of directory names to exclude
        ignore_patterns (list): List of ignore patterns (like from .gitignore)
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if ignore_patterns is None:
        ignore_patterns = []

    structure = {}
    extensions_set = set()

    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)

        if item in exclude_dirs or should_exclude(item_path, ignore_patterns, root_dir):
            continue

        if os.path.isdir(item_path):
            substructure, sub_extensions = get_directory_structure(
                item_path, exclude_dirs, ignore_patterns
            )
            structure[item] = substructure
            extensions_set.update(sub_extensions)
        else:
            structure.setdefault("_files", []).append(item)
            _, ext = os.path.splitext(item)
            if ext:
                extensions_set.add(ext.lower())

    return structure, extensions_set


def sort_files_by_type(files):
    """Sort files by extension and then by name."""
    return sorted(files, key=lambda f: (os.path.splitext(f)[1], f.lower()))


def build_tree(structure, tree, color_map, parent_name="Root"):
    """Build the tree structure with colored file names."""
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


def display_tree(root_dir, exclude_dirs=None, ignore_file=None):
    """Display the directory tree with color-coded file types.

    Args:
        root_dir (str): Root directory path to display
        exclude_dirs (list): List of directory names to exclude from the tree
        ignore_file (str): Path to ignore file (like .gitignore)
    """
    if exclude_dirs is None:
        exclude_dirs = []

    ignore_patterns = []
    if ignore_file:
        ignore_file_path = os.path.join(root_dir, ignore_file)
        ignore_patterns = parse_ignore_file(ignore_file_path)

    structure, extensions = get_directory_structure(
        root_dir, exclude_dirs, ignore_patterns
    )

    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}

    console = Console()
    tree = Tree(f"📂 {os.path.basename(root_dir)}")
    build_tree(structure, tree, color_map)
    console.print(tree)


if __name__ == "__main__":
    project_path = input("Enter the project directory path: ").strip()

    exclude_input = input(
        "Enter directories to exclude (comma-separated) or press Enter to skip: "
    ).strip()
    exclude_dirs = (
        [d.strip() for d in exclude_input.split(",")] if exclude_input else []
    )

    ignore_file = input(
        "Enter ignore file name (e.g., .gitignore) or press Enter to skip: "
    ).strip()

    if os.path.exists(project_path) and os.path.isdir(project_path):
        display_tree(project_path, exclude_dirs, ignore_file)
    else:
        print("Invalid directory path. Please enter a valid path.")
