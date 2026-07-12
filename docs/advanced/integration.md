# Integration with Other Tools

Recursivist fits naturally into existing workflows. This guide covers the most useful integrations.

## Git

### Use Your `.gitignore`

Filter the tree with a repository's existing ignore rules:

```bash
recursivist visualize --ignore-file .gitignore
```

### Scan a Repository by URL

`visualize`, `export`, and `compare` also take a GitHub repository URL in place of a local path, downloading the repository to a temporary directory and scanning it in place — no manual clone required:

```bash
recursivist export https://github.com/owner/repo --format md --output-dir ./docs
```

A `/tree/<ref>` or `/blob/<ref>/<subpath>` selector pins a branch, tag, or commit and, optionally, a subtree. In CI or against private repositories, set `GITHUB_TOKEN` (or `GH_TOKEN`) to raise rate limits and authenticate. See the [CLI Reference](../reference/cli-reference.md#github-repositories) for the accepted URL forms.

### Pre-commit Framework

Recursivist ships an official [pre-commit](https://pre-commit.com) hook (id `recursivist-export`) that regenerates an export before every commit. Add it to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/ArmaanjeetSandhu/recursivist
    rev: v2.1.0 # use the latest release tag
    hooks:
      - id: recursivist-export
        args:
          - "."
          - "--format"
          - "md"
          - "--output-dir"
          - "docs"
          - "--prefix"
          - "structure"
          - "--exclude"
          - "node_modules .git venv"
```

Then enable it:

```bash
pre-commit install
```

### Manual Git Hook

Without the framework, a `.git/hooks/pre-commit` script works too:

```bash
#!/bin/bash
recursivist export --format md --exclude node_modules --exclude .git --prefix STRUCTURE --sort-by-loc
git add STRUCTURE.md
```

Make it executable with `chmod +x .git/hooks/pre-commit`.

## Processing JSON with jq

The JSON export pairs well with [jq](https://jqlang.org). Export with the detail flags you need (each file then becomes an object with `path`, `loc`, and/or `size`):

```bash
recursivist export --format json --prefix structure --sort-by-loc --size
```

```bash
# Count files by extension
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object") | (.path | split(".") | .[-1]) | ascii_downcase' \
  structure.json | sort | uniq -c | sort -nr

# Ten largest files
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object" and has("size")) | [.size, .path] | @tsv' \
  structure.json | sort -nr | head -10

# Lines of code per top-level directory
jq -r '.structure | to_entries[]
       | select(.value | type == "object" and has("_loc"))
       | [.key, (.value._loc | tostring)] | @tsv' structure.json | sort -k2 -nr
```

## Python

Recursivist's modules can be used directly. Scanning produces the nested structure dictionary; `get_exporter` writes files:

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

print("Total lines of code:", structure.get("_loc", 0))
print("Total size (bytes):", structure.get("_size", 0))
```

Each entry in a directory's `_files` list is a `FileEntry` (a `NamedTuple`); use `FileEntry.coerce(...)` to normalize a raw entry, then read attributes like `.name`, `.path`, and `.loc`. Because `FileEntry` subclasses `tuple`, tuple-style access and `isinstance(item, tuple)` still work. See the [API Reference](../reference/api-reference.md) for a complete example.

### Serving Structures from Flask

```python
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
        return jsonify({"directory": directory, "structure": structure})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
```

## Continuous Integration

### GitHub Actions

```yaml
name: Generate Project Structure Documentation

on:
  push:
    branches: [main]
    paths-ignore:
      - "docs/structure.md"

jobs:
  update-structure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install recursivist
      - run: |
          mkdir -p docs
          recursivist export --format md \
            --exclude node_modules --exclude .git \
            --output-dir ./docs --prefix structure --sort-by-loc
      - run: |
          git config user.email "action@github.com"
          git config user.name "GitHub Action"
          git add docs/structure.md
          git diff --quiet && git diff --staged --quiet || git commit -m "Update structure docs"
          git push
```

### GitLab CI

```yaml
generate-structure:
  image: python:3.12-slim
  script:
    - pip install recursivist
    - mkdir -p docs
    - recursivist export --format md --exclude node_modules --exclude .git --output-dir ./docs --prefix structure --sort-by-loc
  artifacts:
    paths:
      - docs/structure.md
```

## Documentation Tools

For MkDocs, Sphinx, or any Markdown-based site, generate a Markdown export and include it like any other page:

```bash
recursivist export --format md --output-dir ./docs --prefix structure
```

Then reference `structure.md` from your navigation (MkDocs) or include it in a source document (Sphinx via the MyST parser).

## Shell Automation

Recursivist works well in scripts. For example, export a structure for every project in a directory:

```bash
#!/bin/bash
for dir in projects/*/; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  recursivist export "$dir" --format md --output-dir ./reports --prefix "$name" --sort-by-loc
done
```

Because Recursivist returns standard exit codes (`0` success, `1` error), these steps compose cleanly with other tooling.
