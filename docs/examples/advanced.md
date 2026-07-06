# Advanced Examples

More involved workflows that combine Recursivist with other tools. For everyday usage, start with [Basic Examples](basic.md).

## Codebase Analysis with jq

Export a detailed JSON tree, then mine it with [jq](https://jqlang.org). With a detail flag enabled, every file is an object carrying `path`, `loc`, and/or `size`:

```bash
recursivist export --format json --full-path \
  --exclude "node_modules .git" \
  --prefix structure --sort-by-loc --size
```

```bash
# Total lines of code
jq '.structure._loc // 0' structure.json

# Lines of code by extension
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object" and has("loc"))
       | "\(.path | split(".") | .[-1])\t\(.loc)"' structure.json \
  | awk -F'\t' '{loc[$1]+=$2; n[$1]++}
      END {for (e in loc) printf "%-6s %8d lines in %d files\n", e, loc[e], n[e]}' \
  | sort -k2 -nr

# Ten largest files by size
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object" and has("size")) | [.size, .path] | @tsv' \
  structure.json | sort -nr | head -10
```

## Focusing on Recent or Similar Files

```bash
# Recently modified source, excluding noise
recursivist visualize --exclude "node_modules .git dist" --sort-by-mtime

# Group files with similar names together
recursivist visualize --sort-by-similarity
```

Name-similarity grouping places `main.py` next to `main.js`, and `test_api.py` next to `test_api.js`:

```
📁 project
├── 📄 main.js
├── 📄 main.py
├── 📄 test_api.py
├── 📄 test_api.js
└── 📄 README.md
```

## Keeping Structure Docs Up to Date

### Pre-commit Framework

Recursivist ships a [pre-commit](https://pre-commit.com) hook that regenerates an export before each commit. Add it to `.pre-commit-config.yaml`:

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

Then run `pre-commit install`. See [Integration](../advanced/integration.md#pre-commit-framework) for details.

### Manual Git Hook

Without the framework, a `.git/hooks/pre-commit` script works too:

```bash
#!/bin/bash
recursivist export --format md --exclude "node_modules .git" --prefix STRUCTURE --sort-by-loc
git add STRUCTURE.md
```

Make it executable with `chmod +x .git/hooks/pre-commit`.

## Continuous Integration

A GitHub Actions workflow that regenerates structure docs on every push to `main`:

```yaml
name: Update Structure Documentation

on:
  push:
    branches: [main]

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
            --exclude "node_modules .git" \
            --output-dir ./docs --prefix structure --sort-by-loc
      - run: |
          git config user.email "action@github.com"
          git config user.name "GitHub Action"
          git add docs/structure.md
          git diff --quiet && git diff --staged --quiet || git commit -m "Update structure docs"
          git push
```

## Multi-Level Project Map

Generate overviews at several depths:

```bash
mkdir -p project-map
recursivist export --format md --depth 1 --output-dir project-map --prefix L1-overview --sort-by-size
recursivist export --format md --depth 2 --output-dir project-map --prefix L2-structure --sort-by-loc
recursivist export --format md --output-dir project-map --prefix L3-complete --sort-by-loc --mtime
```

## Embedding a React Component

Export a component, then wrap it in your app. The generated `DirectoryViewer` is self-contained:

```bash
recursivist export --format jsx \
  --exclude "node_modules .git" \
  --output-dir ./src/components --prefix DirectoryViewer --sort-by-loc
```

```jsx
// src/App.jsx
import DirectoryViewer from "./components/DirectoryViewer";

export default function App() {
  return (
    <main>
      <h1>Project Structure</h1>
      <DirectoryViewer />
    </main>
  );
}
```

Remember to `npm install lucide-react prop-types` and ensure Tailwind CSS is available (or adapt the class names).
