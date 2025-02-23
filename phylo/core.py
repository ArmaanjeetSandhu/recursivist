import os
from rich.tree import Tree
from rich.console import Console
from rich.text import Text
import colorsys
import hashlib


def generate_color_for_extension(extension):
    """Generate a consistent color for a given file extension."""
    if not extension:
        return "#FFFFFF"

    hash_value = int(hashlib.md5(extension.encode()).hexdigest(), 16)
    hue = hash_value % 360 / 360.0

    saturation = 0.7
    value = 0.95

    rgb = colorsys.hsv_to_rgb(hue, saturation, value)

    hex_color = "#{:02x}{:02x}{:02x}".format(
        int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
    )
    return hex_color


def get_directory_structure(root_dir, exclude_dirs=None):
    """Build a nested dictionary representing the directory structure.

    Args:
        root_dir (str): Root directory path to start from
        exclude_dirs (list): List of directory names to exclude
    """
    if exclude_dirs is None:
        exclude_dirs = []

    structure = {}
    extensions_set = set()

    for item in os.listdir(root_dir):
        if item in exclude_dirs:
            continue

        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path):
            substructure, sub_extensions = get_directory_structure(
                item_path, exclude_dirs
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
    for folder, content in structure.items():
        if folder == "_files":
            for file in sort_files_by_type(content):
                ext = os.path.splitext(file)[1].lower()
                color = color_map.get(ext, "#FFFFFF")
                colored_text = Text(f"📄 {file}", style=color)
                tree.add(colored_text)
        else:
            subtree = tree.add(f"📁 {folder}")
            build_tree(content, subtree, color_map, folder)


def display_tree(root_dir, exclude_dirs=None):
    """Display the directory tree with color-coded file types.

    Args:
        root_dir (str): Root directory path to display
        exclude_dirs (list): List of directory names to exclude from the tree
    """
    if exclude_dirs is None:
        exclude_dirs = []

    structure, extensions = get_directory_structure(root_dir, exclude_dirs)

    color_map = {ext: generate_color_for_extension(ext) for ext in extensions}

    console = Console()
    tree = Tree(f"📂 {os.path.basename(root_dir)}")
    build_tree(structure, tree, color_map)
    console.print(tree)


if __name__ == "__main__":
    project_path = input("Enter the project directory path: ").strip()

    exclude_input = input(
        "Enter directories to exclude (separated by space), or press Enter to skip: "
    ).strip()
    exclude_dirs = (
        [d.strip() for d in exclude_input.split(" ")] if exclude_input else []
    )

    if os.path.exists(project_path) and os.path.isdir(project_path):
        display_tree(project_path, exclude_dirs)
    else:
        print("Invalid directory path. Please enter a valid path.")
