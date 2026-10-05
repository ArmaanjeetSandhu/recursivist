# Scripting and Python

Recursivist is easy to drive from a shell script, and its modules can be imported directly from Python.

## Shell Scripts

Export a structure for every project in a directory:

```bash
#!/bin/bash
for dir in projects/*/; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  recursivist export "$dir" --format md --output-dir ./reports --prefix "$name" --sort-by-loc
done
```

Recursivist returns standard [exit codes](../user-guide/basic-usage.md#exit-codes) (`0` for success, non-zero for failure), so these steps compose cleanly with `&&`, `set -e`, and CI runners.

The `config` subcommands that print a value write nothing else to standard output, so their output can be captured:

```bash
# Export with your saved icon style instead of the export default
recursivist export --icon-style "$(recursivist config get icon-style)"

# Show your saved preferences
cat "$(recursivist config path)"

# Read the settings in effect for a project as JSON
recursivist config list ./my-project --json
```

## Using Recursivist from Python

Scanning produces a tree of `Directory` nodes; `get_exporter` writes files from it:

```python
from recursivist.scanner import get_directory_structure
from recursivist.exporters import get_exporter
from recursivist.flags import DisplayOptions

structure, extensions = get_directory_structure(
    "path/to/directory",
    exclude_dirs=["node_modules", ".git"],
    exclude_extensions={".pyc", ".log"},
    sort_by_loc=True,
    sort_by_size=True,
)

# A DisplayOptions describes how to sort and what to annotate.
spec = DisplayOptions(sort_key="loc", metrics=("loc", "size"))
for fmt, out in (("md", "output.md"), ("json", "output.json")):
    get_exporter(
        fmt,
        structure=structure,
        root_name="path/to/directory",
        spec=spec,
    ).export(out)

print("Total lines of code:", structure.loc)
print("Total size (bytes):", structure.size)
```

Each entry in a directory's `files` list is a `FileEntry` (a `NamedTuple`); read attributes like `.name`, `.path`, and `.loc` directly. Because `FileEntry` subclasses `tuple`, tuple-style access and `isinstance(item, tuple)` work as well. Subdirectories are nested `Directory` nodes under `subdirectories`, keyed by name. The [Python API reference](../reference/api-reference.md#the-directory-structure) describes every field and has a longer example.

## Serving Structures from Flask

```python
from dataclasses import asdict

from flask import Flask, jsonify, request
from recursivist.scanner import get_directory_structure

app = Flask(__name__)


@app.route("/api/directory-structure")
def get_structure():
    directory = request.args.get("directory", ".")
    exclude = request.args.get("exclude_dirs", "")
    exclude_dirs = exclude.split(",") if exclude else []
    try:
        structure, _ = get_directory_structure(
            directory,
            exclude_dirs=exclude_dirs,
            max_depth=int(request.args.get("max_depth", 0)),
            sort_by_loc="sort_by_loc" in request.args,
            sort_by_size="sort_by_size" in request.args,
        )
        return jsonify({"directory": directory, "structure": asdict(structure)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

!!! warning

    This endpoint lists whatever directory the caller names. Restrict `directory` to a known root before exposing anything like it beyond your own machine.
