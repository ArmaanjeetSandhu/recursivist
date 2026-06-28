# API Reference

Recursivist is organized as a set of focused modules that can be used directly from Python. This page documents the public API (generated from the source docstrings) and shows how to compose it.

## Module Overview

| Module                   | Responsibility                                      |
| ------------------------ | --------------------------------------------------- |
| `recursivist.scanner`    | Walk a directory into the nested structure dict     |
| `recursivist.tree`       | Render a structure as a Rich tree in the terminal   |
| `recursivist.exporters`  | Exporter registry and per-format exporters          |
| `recursivist.compare`    | Compare and render two structures                   |
| `recursivist.filtering`  | Ignore-file, glob, and regex exclusion logic        |
| `recursivist.sorting`    | File ordering (by type, metric, or name similarity) |
| `recursivist.metrics`    | Lines of code, size, mtime, and metric formatting   |
| `recursivist.colors`     | Deterministic per-extension colors                  |
| `recursivist.icons`      | Emoji and Nerd Font icon lookup                     |
| `recursivist.git_status` | Git status lookup                                   |
| `recursivist.config`     | User-configuration persistence                      |

## The Structure Dictionary

Most of the API revolves around the nested dictionary produced by `get_directory_structure`. Each subdirectory is a nested dict under its own name; a directory's own files and aggregate metrics live under reserved keys:

- `_files`: a list of [`FileEntry`](#fileentry) objects for the directory's files
- `_loc`, `_size`, `_mtime`: aggregate totals, present only when the matching metric is requested
- `_max_depth_reached`: present when traversal stopped at the depth limit
- `_git_markers`: a `{filename: status}` map, present only with Git status enabled

### FileEntry

::: recursivist._models.FileEntry

## Scanner

::: recursivist.scanner

## Tree Rendering

::: recursivist.tree

## Exporters

Exports go through the `get_exporter` factory, which returns a `BaseExporter` subclass for the requested format. Call its `export` method with an output path.

::: recursivist.exporters

::: recursivist.exporters.base

## Compare

::: recursivist.compare

## Filtering

::: recursivist.filtering

## Sorting

::: recursivist.sorting

## Metrics

::: recursivist.metrics

## Colors

::: recursivist.colors

## Icons

::: recursivist.icons

## Git Status

::: recursivist.git_status

## Configuration

::: recursivist.config

## Example: Custom Analysis Script

This script scans a directory with metrics enabled, exports two formats, and prints a summary:

```python
import sys

from recursivist.scanner import get_directory_structure
from recursivist.exporters import get_exporter
from recursivist._models import FileEntry


def analyze_directory(directory_path: str) -> None:
    # Scan with lines-of-code and size tracking enabled
    structure, extensions = get_directory_structure(
        directory_path,
        exclude_dirs=["node_modules", ".git", ".venv"],
        exclude_extensions={".pyc", ".log", ".tmp"},
        sort_by_loc=True,
        sort_by_size=True,
    )

    # Export to multiple formats via the factory
    for fmt, out in (("md", "analysis.md"), ("json", "analysis.json")):
        exporter = get_exporter(
            fmt,
            structure=structure,
            root_name=directory_path,
            sort_by_loc=True,
            sort_by_size=True,
        )
        exporter.export(out)

    print(f"Directory: {directory_path}")
    print(f"Extensions: {sorted(extensions)}")
    print(f"Total lines of code: {structure.get('_loc', 0)}")
    print(f"Total size (bytes): {structure.get('_size', 0)}")

    # Collect every file as a FileEntry and find the largest by LOC
    def collect(struct: dict, path: str = "") -> list[tuple[str, FileEntry]]:
        found: list[tuple[str, FileEntry]] = []
        for entry in struct.get("_files", []):
            fe = FileEntry.from_raw(entry, sort_by_loc=True, sort_by_size=True)
            found.append((f"{path}/{fe.name}" if path else fe.name, fe))
        for name, content in struct.items():
            if isinstance(content, dict) and not name.startswith("_"):
                found.extend(collect(content, f"{path}/{name}" if path else name))
        return found

    files = collect(structure)
    files.sort(key=lambda item: item[1].loc, reverse=True)

    print("\nTop 5 files by lines of code:")
    for display_path, fe in files[:5]:
        print(f"  {fe.loc:>6} {display_path}")


if __name__ == "__main__":
    analyze_directory(sys.argv[1] if len(sys.argv) > 1 else ".")
```

## Extending Recursivist

The modular layout makes the common extension points clear:

- **A new export format**: subclass `BaseExporter` in a new module under `recursivist/exporters/`, implement `export`, and register it in the `_EXPORTERS` map in `recursivist/exporters/__init__.py`.
- **Custom filtering**: extend `should_exclude` in `recursivist/filtering.py`.
- **Custom rendering**: build on `build_tree` and `display_tree` in `recursivist/tree.py`.
- **A new metric**: collect it in `get_directory_structure` (`recursivist/scanner.py`), thread it through `FileEntry`, and surface it in the renderers, exporters, and CLI.

See the [Development Guide](../advanced/development.md) for the full workflow.
