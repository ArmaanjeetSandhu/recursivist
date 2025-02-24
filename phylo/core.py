import os
from rich.tree import Tree
from rich.console import Console
from rich.text import Text
from exports import DirectoryExporter
import colorsys
import hashlib
import fnmatch
from pathlib import Path


def export_structure(structure, root_dir, format_type, output_path):
    """Export the directory structure to various formats.

    Args:
        structure (dict): Directory structure dictionary
        root_dir (str): Root directory name
        format_type (str): Export format ('txt', 'json', 'html', or 'md')
        output_path (str): Path where the export file will be saved
    """
    exporter = DirectoryExporter(structure, os.path.basename(root_dir))

    format_map = {
        "txt": exporter.to_txt,
        "json": exporter.to_json,
        "html": exporter.to_html,
        "md": exporter.to_markdown,
    }

    if format_type.lower() not in format_map:
        raise ValueError(f"Unsupported format: {format_type}")

    export_func = format_map[format_type.lower()]
    export_func(output_path)


def parse_ignore_file(ignore_file_path):
    """Parse an ignore file (like .gitignore) and return patterns."""
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


def should_exclude(path, ignore_context, exclude_extensions=None):
    """Check if a path should be excluded based on ignore patterns and extensions.

    Args:
        path (str): Path to check
        ignore_context (dict): Dictionary with 'patterns' and 'current_dir' keys
        exclude_extensions (set): Set of file extensions to exclude

    Returns:
        bool: True if path should be excluded
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


def get_directory_structure(
    root_dir,
    exclude_dirs=None,
    ignore_file=None,
    exclude_extensions=None,
    parent_ignore_patterns=None,
):
    """Build a nested dictionary representing the directory structure.

    Args:
        root_dir (str): Root directory path to start from
        exclude_dirs (list): List of directory names to exclude
        ignore_file (str): Name of ignore file (like .gitignore)
        exclude_extensions (set): Set of file extensions to exclude
        parent_ignore_patterns (list): Patterns from parent directories
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

    for item in os.listdir(root_dir):
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


def display_tree(
    root_dir, exclude_dirs=None, ignore_file=None, exclude_extensions=None
):
    """Display the directory tree with color-coded file types.

    Args:
        root_dir (str): Root directory path to display
        exclude_dirs (list): List of directory names to exclude from the tree
        ignore_file (str): Name of ignore file (like .gitignore)
        exclude_extensions (set): Set of file extensions to exclude (e.g., {'.pyc', '.log'})
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


if __name__ == "__main__":
    project_path = input("Enter the project directory path: ").strip()

    exclude_input = input(
        "Enter directories to exclude (space-separated) or press Enter to skip: "
    ).strip()
    exclude_dirs = (
        [d.strip() for d in exclude_input.split(" ")] if exclude_input else []
    )

    extensions_input = input(
        "Enter file extensions to exclude (space-separated, with or without dots) or press Enter to skip: "
    ).strip()
    exclude_extensions = (
        set(ext.strip() for ext in extensions_input.split(" "))
        if extensions_input
        else set()
    )

    ignore_file = input(
        "Enter ignore file name (e.g., .gitignore) or press Enter to skip: "
    ).strip()

    if not os.path.exists(project_path) or not os.path.isdir(project_path):
        print("Invalid directory path. Please enter a valid path.")
        exit(1)

    structure, _ = get_directory_structure(
        project_path,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
    )

    display_tree(project_path, exclude_dirs, ignore_file, exclude_extensions)

    export_format = (
        input("Export format (txt/json/html/md) or press Enter to skip: ")
        .strip()
        .lower()
    )

    if export_format:
        if export_format not in ["txt", "json", "html", "md"]:
            print("Unsupported format. Skipping export.")
        else:
            root_name = os.path.basename(project_path)
            output_path = f"structure.{export_format}"

            try:
                export_structure(structure, project_path, export_format, output_path)
                print(f"Successfully exported to {output_path}")
            except Exception as e:
                print(f"Error during export: {e}")
