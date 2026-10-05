# Python API

Recursivist is organized as a set of focused modules that can be imported directly from Python. These pages are generated from the source docstrings; this one maps the modules and describes the data they share.

## Modules

| Module                   | Responsibility                                      | Reference                                             |
| ------------------------ | --------------------------------------------------- | ----------------------------------------------------- |
| `recursivist.scanner`    | Walk a directory into a tree of `Directory` nodes   | [Scanning and Filtering](api/scanning.md)             |
| `recursivist.filtering`  | Ignore-file, glob, and regex exclusion logic        | [Scanning and Filtering](api/scanning.md)             |
| `recursivist.flags`      | Resolve sort/display flags into a `DisplayOptions`  | [Sorting and Metrics](api/display.md)                 |
| `recursivist.sorting`    | File ordering (by type, metric, or name similarity) | [Sorting and Metrics](api/display.md)                 |
| `recursivist.metrics`    | Lines of code, size, mtime, and metric formatting   | [Sorting and Metrics](api/display.md)                 |
| `recursivist.tree`       | Render a structure as a Rich tree in the terminal   | [Rendering](api/rendering.md)                         |
| `recursivist.compare`    | Compare and render two structures                   | [Rendering](api/rendering.md)                         |
| `recursivist.colors`     | Deterministic per-extension colors                  | [Rendering](api/rendering.md)                         |
| `recursivist.icons`      | Emoji and Nerd Font icon lookup                     | [Rendering](api/rendering.md)                         |
| `recursivist.exporters`  | Exporter registry and per-format exporters          | [Exporters](api/exporters.md)                         |
| `recursivist.git_status` | Git status lookup                                   | [Git, GitHub, and Configuration](api/integrations.md) |
| `recursivist.github`     | Materialize a GitHub repository for scanning        | [Git, GitHub, and Configuration](api/integrations.md) |
| `recursivist.config`     | User and project configuration                      | [Git, GitHub, and Configuration](api/integrations.md) |

## The Directory Structure

Most of the API revolves around the tree produced by [`get_directory_structure`][recursivist.scanner.get_directory_structure]: a [`Directory`][recursivist._models.Directory] for the scanned root, with every subdirectory nested as another `Directory`. Each one holds its own data in these fields:

- `files`: a list of [`FileEntry`][recursivist._models.FileEntry] objects for the directory's files
- `subdirectories`: the nested directories, as a `{name: Directory}` map
- `loc`, `size`, `mtime`: aggregate totals, `None` unless the matching metric is requested
- `max_depth_reached`: `True` when traversal stopped at the depth limit
- `hidden_contents`: `True` alongside `max_depth_reached` when the untraversed directory is not empty, so renderers can tell it apart from one that holds nothing
- `symlink_loop`: `True` when a directory was not descended into because it resolves to one of its own ancestors
- `git_markers`: a `{filename: status}` map, empty unless Git status is enabled

Subdirectory names are the only keys of `subdirectories`, so a directory can be called anything. [`iter_subdirectories`][recursivist.scanner.iter_subdirectories] yields them in the order the renderers list them.

## DisplayOptions

Sorting and annotation are driven by a single resolved value, [`DisplayOptions`][recursivist.flags.DisplayOptions], which the renderers and exporters consult. It separates ordering (`sort_key`) from annotation (`metrics` and `show_git_status`):

```python
from recursivist.flags import DisplayOptions

# Sort by lines of code; annotate each file with LOC then size
spec = DisplayOptions(sort_key="loc", metrics=("loc", "size"))
```

`sort_key` is one of `"loc"`, `"size"`, `"mtime"`, `"git_status"`, `"similarity"`, or `None` (the default extension/name order). `metrics` is the ordered tuple of numeric metrics to display, and `show_git_status` toggles the Git-status marker. To build a `DisplayOptions` from raw CLI flags, use [`resolve_display_options`][recursivist.flags.resolve_display_options], passing the flag ids in the order they were given as `order`.

## Example: Custom Analysis Script

This script scans a directory with metrics enabled, exports two formats, and prints a summary:

```python
import sys

from recursivist.scanner import get_directory_structure, iter_subdirectories
from recursivist.exporters import get_exporter
from recursivist.flags import DisplayOptions
from recursivist._models import Directory, FileEntry


def analyze_directory(directory_path: str) -> None:
    # Scan with lines-of-code and size tracking enabled
    structure, extensions = get_directory_structure(
        directory_path,
        exclude_dirs=["node_modules", ".git", ".venv"],
        exclude_extensions={".pyc", ".log", ".tmp"},
        sort_by_loc=True,
        sort_by_size=True,
    )

    # Describe how to sort and annotate, then export via the factory.
    # Here: order by lines of code, annotating each file with LOC then size.
    spec = DisplayOptions(sort_key="loc", metrics=("loc", "size"))
    for fmt, out in (("md", "analysis.md"), ("json", "analysis.json")):
        exporter = get_exporter(
            fmt,
            structure=structure,
            root_name=directory_path,
            spec=spec,
        )
        exporter.export(out)

    print(f"Directory: {directory_path}")
    print(f"Extensions: {sorted(extensions)}")
    print(f"Total lines of code: {structure.loc}")
    print(f"Total size (bytes): {structure.size}")

    # Collect every file (each a FileEntry) and find the largest by LOC.
    def collect(directory: Directory, path: str = "") -> list[tuple[str, FileEntry]]:
        found: list[tuple[str, FileEntry]] = []
        for fe in directory.files:
            found.append((f"{path}/{fe.name}" if path else fe.name, fe))
        for name, subdirectory in iter_subdirectories(directory):
            found.extend(collect(subdirectory, f"{path}/{name}" if path else name))
        return found

    files = collect(structure)
    files.sort(key=lambda item: item[1].loc, reverse=True)

    print("\nTop 5 files by lines of code:")
    for display_path, fe in files[:5]:
        print(f"  {fe.loc:>6} {display_path}")


if __name__ == "__main__":
    analyze_directory(sys.argv[1] if len(sys.argv) > 1 else ".")
```

For a shorter starting point, see [Scripting and Python](../recipes/scripting.md#using-recursivist-from-python). To add an export format, a metric, or a command of your own, see [Extending Recursivist](../contributing/development.md#extending-recursivist).
