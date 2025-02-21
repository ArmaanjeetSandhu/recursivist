import os
import json


def get_directory_structure(root_dir):
    """Recursively gets the directory structure as a nested dictionary."""
    dir_structure = {}
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path):
            dir_structure[item] = get_directory_structure(item_path)
        else:
            dir_structure[item] = None
    return dir_structure


def save_to_json(root_dir, output_file="project_structure.json"):
    structure = get_directory_structure(root_dir)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=4)
    print(f"Project structure saved to {output_file}")


if __name__ == "__main__":
    project_path = input("Enter the project directory path: ").strip()
    if os.path.exists(project_path) and os.path.isdir(project_path):
        save_to_json(project_path)
    else:
        print("Invalid directory path. Please enter a valid path.")
