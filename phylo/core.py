import os
import json
from rich.tree import Tree
from rich.console import Console


def get_directory_structure(root_dir):
    structure = {}
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path):
            structure[item] = get_directory_structure(item_path)
        else:
            structure.setdefault("_files", []).append(item)
    return structure


def build_tree(structure, tree, parent_name="Root"):
    for folder, content in structure.items():
        if folder == "_files":
            for file in content:
                tree.add(f"📄 {file}")
        else:
            subtree = tree.add(f"📁 {folder}")
            build_tree(content, subtree, folder)


def display_tree(root_dir):
    structure = get_directory_structure(root_dir)
    console = Console()
    tree = Tree(f"📂 {os.path.basename(root_dir)}")
    build_tree(structure, tree)
    console.print(tree)


if __name__ == "__main__":
    project_path = input("Enter the project directory path: ").strip()
    if os.path.exists(project_path) and os.path.isdir(project_path):
        display_tree(project_path)
    else:
        print("Invalid directory path. Please enter a valid path.")
