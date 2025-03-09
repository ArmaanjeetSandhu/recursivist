# API Reference

This page provides documentation for Recursivist's Python API, automatically generated from the source code's docstrings, which can be used to integrate directory visualization and analysis capabilities into your own Python applications.

## Core Module

::: recursivist.core

## Exports Module

::: recursivist.exports

## Compare Module

::: recursivist.compare

## JSX Export Module

::: recursivist.jsx_export

## Using the Python API in Custom Scripts

Here's an example of how to use the Python API to create a custom directory analysis script:

```python
import sys
from recursivist.core import get_directory_structure
from recursivist.core import export_structure

def analyze_directory(directory_path):
    # Get directory structure with line counts and file sizes
    structure, extensions = get_directory_structure(
        directory_path,
        exclude_dirs=["node_modules", ".git", "venv"],
        exclude_extensions={".pyc", ".log", ".tmp"},
        sort_by_loc=True,
        sort_by_size=True
    )

    # Export to multiple formats
    export_structure(structure, directory_path, "md", "analysis.md", sort_by_loc=True, sort_by_size=True)
    export_structure(structure, directory_path, "json", "analysis.json", sort_by_loc=True, sort_by_size=True)

    # Calculate some statistics
    total_loc = structure.get("_loc", 0)
    total_size = structure.get("_size", 0)

    print(f"Directory: {directory_path}")
    print(f"Total lines of code: {total_loc}")
    print(f"Total size: {total_size} bytes")

    # Find the files with the most lines of code
    def collect_files(structure, path=""):
        files = []
        for name, content in structure.items():
            if name == "_files":
                for file_item in content:
                    if isinstance(file_item, tuple) and len(file_item) > 2:
                        file_name, full_path, loc = file_item[0], file_item[1], file_item[2]
                        files.append((file_name, full_path, loc))
            elif isinstance(content, dict) and name not in ["_max_depth_reached", "_loc", "_size", "_mtime"]:
                files.extend(collect_files(content, f"{path}/{name}"))
        return files

    files = collect_files(structure)
    files.sort(key=lambda x: x[2], reverse=True)

    print("\nTop 5 files by lines of code:")
    for i, (name, path, loc) in enumerate(files[:5], 1):
        print(f"{i}. {path} ({loc} lines)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_directory(sys.argv[1])
    else:
        analyze_directory(".")
```

## API Extension Points

If you're looking to extend Recursivist's functionality, these are the main extension points:

1. **Custom Pattern Matching**: Extend the `should_exclude` function in `core.py`
2. **New Export Format**: Add a new method to the `DirectoryExporter` class in `exports.py`
3. **Custom Visualization**: Modify the `build_tree` and `display_tree` functions in `core.py`
4. **Custom Statistics**: Add new statistics collection to the `get_directory_structure` function

The API is designed to be modular, making it possible to reuse individual components for custom functionality while maintaining consistent behavior across the library.
