# Integration with Other Tools

Recursivist can be integrated with other tools and workflows to enhance productivity. This guide provides examples and guidance on various integration options.

## Using with Git Repositories

### Gitignore Integration

When working with Git repositories, you can use your existing `.gitignore` file to filter the directory structure:

```bash
recursivist visualize --ignore-file .gitignore
```

This is particularly useful for quickly visualizing the structure of a Git repository without the noise of ignored files.

### Pre-commit Framework

Recursivist provides official support for the [pre-commit](https://pre-commit.com) framework. This is the easiest way to ensure your directory structure documentation is always up to date before every commit.

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/ArmaanjeetSandhu/recursivist
    rev: v1.4.8 # Replace with the latest version tag
      - id: recursivist-export
        # Customize your export settings here
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

Once added, run `pre-commit install` to enable it. Now, whenever you commit changes, Recursivist will automatically regenerate your structure files!

### Manual Git Hooks

If you aren't using the `pre-commit` framework, you can still use Recursivist in standard Git hooks to automatically document your project structure:

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Update project structure documentation when committing
if git diff --cached --name-only | grep -q -v "STRUCTURE.md"; then
  echo "Updating project structure documentation..."

  # Generate updated structure with LOC statistics
  recursivist export --format md --prefix "STRUCTURE" --sort-by-loc

  # Add to commit if changed
  git add STRUCTURE.md
fi
```

Make the hook executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Git Workflow Scripts

This script compares two Git branches:

```bash
#!/bin/bash

# Compare two Git branches
current_branch=$(git rev-parse --abbrev-ref HEAD)
compare_branch=${1:-main}

# Create temporary directories
mkdir -p .tmp/$current_branch .tmp/$compare_branch

# Extract current branch files
git archive --format=tar $current_branch | tar -xf - -C .tmp/$current_branch/

# Extract comparison branch files
git archive --format=tar $compare_branch | tar -xf - -C .tmp/$compare_branch/

# Compare the branches with statistics
recursivist compare .tmp/$current_branch .tmp/$compare_branch \
  --save \
  --prefix "branch-comparison" \
  --sort-by-loc

# Clean up
rm -rf .tmp

echo "Branch comparison saved to branch-comparison.html"
```

## Processing JSON Exports with jq

The JSON export format works well with command-line data processors like [jq](https://jqlang.org). Here are some useful examples:

### Count Files by Extension

```bash
# Export structure to JSON with file statistics
recursivist export --format json --prefix structure --sort-by-loc

# Count files by extension and sort by count
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] |
    select(type=="object") |
    (.path | split(".") | .[-1]) |
    ascii_downcase' structure.json | sort | uniq -c | sort -nr
```

### Find Largest Files

```bash
# Export with file size statistics
recursivist export --format json --prefix structure --sort-by-size

# Get the 10 largest files
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] |
    select(type=="object" and has("size")) |
    [.size, .path] | @tsv' structure.json | sort -nr | head -10
```

### Find Files with Most Lines of Code

```bash
# Export with LOC statistics
recursivist export --format json --prefix structure --sort-by-loc

# Get the 10 files with most lines of code
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] |
    select(type=="object" and has("loc")) |
    [.loc, .path] | @tsv' structure.json | sort -nr | head -10
```

### Analyze Code Distribution by Directory

```bash
# Get lines of code by directory
jq -r '.structure | to_entries[] |
    select(.value | type == "object" and has("_loc")) |
    [.key, (.value._loc | tostring)] | @tsv' structure.json | sort -k2 -nr
```

## Programmatic Use with Python

You can integrate Recursivist directly into your Python applications:

### Basic Directory Analysis

```python
from recursivist.core import get_directory_structure, export_structure

# Get directory structure with statistics
structure, extensions = get_directory_structure(
    "path/to/directory",
    exclude_dirs=["node_modules", ".git"],
    exclude_extensions={".pyc", ".log"},
    sort_by_loc=True,
    sort_by_size=True
)

# Export to multiple formats
export_structure(structure, "path/to/directory", "md", "output.md", sort_by_loc=True, sort_by_size=True)
export_structure(structure, "path/to/directory", "json", "output.json", sort_by_loc=True, sort_by_size=True)

# Calculate statistics
total_loc = structure.get("_loc", 0)
total_size = structure.get("_size", 0)
print(f"Total lines of code: {total_loc}")
print(f"Total size: {total_size} bytes")
```

### Custom File Analysis

```python
from recursivist.core import get_directory_structure

def analyze_file_types(directory):
    """Analyze the distribution of file types in a directory."""
    structure, extensions = get_directory_structure(
        directory,
        exclude_dirs=["node_modules", ".git"],
        sort_by_loc=True
    )

    # Extract all files with their extensions
    files_by_ext = {}

    def process_directory(dir_struct, path=""):
        if "_files" in dir_struct:
            for file_item in dir_struct["_files"]:
                if isinstance(file_item, tuple):
                    filename = file_item[0]
                else:
                    filename = file_item

                ext = filename.split(".")[-1] if "." in filename else "no_extension"
                loc = file_item[2] if isinstance(file_item, tuple) and len(file_item) > 2 else 0

                if ext not in files_by_ext:
                    files_by_ext[ext] = {"count": 0, "loc": 0}

                files_by_ext[ext]["count"] += 1
                files_by_ext[ext]["loc"] += loc

        for name, content in dir_struct.items():
            if isinstance(content, dict) and name not in ["_files", "_max_depth_reached", "_loc", "_size", "_mtime"]:
                process_directory(content, f"{path}/{name}")

    process_directory(structure)

    # Print results
    print(f"File type distribution in {directory}:")
    print("-" * 50)
    print(f"{'Extension':<12} {'Count':<8} {'Lines of Code':<14} {'Avg LOC/File':<12}")
    print("-" * 50)

    for ext, data in sorted(files_by_ext.items(), key=lambda x: x[1]["count"], reverse=True):
        avg_loc = data["loc"] / data["count"] if data["count"] > 0 else 0
        print(f"{ext:<12} {data['count']:<8} {data['loc']:<14} {avg_loc:<12.1f}")

# Usage
analyze_file_types("path/to/project")
```

## Web Application Integration

### Using the React Component Export

Recursivist can export a directory structure as a React component:

```bash
recursivist export --format jsx --output-dir ./src/components --prefix DirectoryViewer --sort-by-loc
```

Then import it into your React application:

```jsx
// src/App.js
import React from "react";
import DirectoryViewer from "./components/DirectoryViewer";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Project Structure</h1>
      </header>
      <main>
        <DirectoryViewer />
      </main>
    </div>
  );
}

export default App;
```

The generated component includes:

- Collapsible folder structure
- Search functionality
- Breadcrumb navigation
- Dark/light mode toggle
- Statistics display when enabled

### Custom API with Flask

You can build a simple API to serve directory structures:

```python
from flask import Flask, jsonify, request
from recursivist.core import get_directory_structure

app = Flask(__name__)

@app.route('/api/directory-structure', methods=['GET'])
def get_structure():
    directory = request.args.get('directory', '.')
    exclude_dirs = request.args.get('exclude_dirs', '').split(',') if request.args.get('exclude_dirs') else []
    max_depth = int(request.args.get('max_depth', 0))

    try:
        structure, _ = get_directory_structure(
            directory,
            exclude_dirs=exclude_dirs,
            max_depth=max_depth,
            sort_by_loc='sort_by_loc' in request.args,
            sort_by_size='sort_by_size' in request.args,
            sort_by_mtime='sort_by_mtime' in request.args
        )
        return jsonify({
            'directory': directory,
            'structure': structure
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
```

## Continuous Integration Integration

You can incorporate Recursivist into your CI/CD pipelines:

### GitHub Actions Example

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
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install Recursivist
        run: pip install recursivist

      - name: Generate structure documentation
        run: |
          mkdir -p docs
          recursivist export \
            --format md \
            --exclude "node_modules .git" \
            --output-dir ./docs \
            --prefix "structure" \
            --sort-by-loc

      - name: Commit and push if changed
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/structure.md
          git diff --quiet && git diff --staged --quiet || git commit -m "Update project structure documentation"
          git push
```

### GitLab CI Example

```yaml
generate-structure:
  image: python:3.10-slim
  script:
    - pip install recursivist
    - mkdir -p docs
    - recursivist export --format md --exclude "node_modules .git" --output-dir ./docs --prefix "structure" --sort-by-loc
  artifacts:
    paths:
      - docs/structure.md
```

## Documentation Tools Integration

### MkDocs Integration

1. Generate a Markdown export:

   ```bash
   recursivist export --format md --output-dir ./docs --prefix "structure"
   ```

2. Include it in your MkDocs navigation:
   ```yaml
   # mkdocs.yml
   nav:
     - Home: index.md
     - Project Structure: structure.md
     # Other pages...
   ```

### Sphinx Integration

Add this to your Sphinx configuration to include the exported structure:

```python
# conf.py
import os
import subprocess

def setup(app):
    app.connect('builder-inited', generate_structure_docs)
    return {'version': '0.1'}

def generate_structure_docs(app):
    # Generate project structure documentation
    subprocess.run([
        'recursivist', 'export',
        '--format', 'md',
        '--exclude', 'node_modules .git _build',
        '--output-dir', './source',
        '--prefix', 'structure',
        '--sort-by-loc'
    ])
```

Then in your RST files:

```rst
Project Structure
================

.. include:: structure.md
   :parser: myst_parser.sphinx_
```

## Shell Script Integration

Recursivist works well with shell scripts for automation:

### Batch Processing Multiple Directories

```bash
#!/bin/bash

# Process multiple directories
for dir in projects/*/; do
  if [ -d "$dir" ]; then
    project_name=$(basename "$dir")
    echo "Processing $project_name..."

    # Export project structure with LOC stats
    recursivist export "$dir" \
      --format md \
      --output-dir ./reports \
      --prefix "$project_name" \
      --sort-by-loc
  fi
done

# Create an index file
echo "# Project Reports" > reports/index.md
echo "" >> reports/index.md
echo "Generated on $(date)" >> reports/index.md
echo "" >> reports/index.md

for file in reports/*.md; do
  if [ "$(basename "$file")" != "index.md" ]; then
    project_name=$(basename "$file" .md)
    echo "- [$project_name]($project_name.md)" >> reports/index.md
  fi
done

echo "Processing complete. Reports are in the ./reports directory."
```

### Weekly Project Evolution Report

```bash
#!/bin/bash

# Get date for filename
date_str=$(date +%Y-%m-%d)

# Create current snapshot
mkdir -p snapshots/current
recursivist export \
  --format json \
  --exclude "node_modules .git snapshots" \
  --output-dir ./snapshots/current \
  --prefix "structure" \
  --sort-by-loc \
  --sort-by-size

# Compare with last week's snapshot if it exists
if [ -f "snapshots/previous/structure.json" ]; then
  echo "Comparing with previous snapshot..."

  # Create comparison
  recursivist compare \
    snapshots/previous snapshots/current \
    --exclude "node_modules .git" \
    --save \
    --output-dir ./reports \
    --prefix "weekly-${date_str}" \
    --sort-by-loc

  echo "Comparison saved to reports/weekly-${date_str}.html"
fi

# Move current to previous for next time
rm -rf snapshots/previous
mv snapshots/current snapshots/previous
```

## Using with Static Analysis Tools

Combine Recursivist with other static analysis tools for comprehensive project insights:

```bash
#!/bin/bash

# Create output directory
mkdir -p analysis

# Generate directory structure with LOC stats
recursivist export \
  --format md \
  --output-dir ./analysis \
  --prefix "structure" \
  --sort-by-loc

# Run additional tools (examples)
# 1. radon for code complexity metrics (Python)
if command -v radon &> /dev/null; then
  echo "Running complexity analysis..."
  radon cc . -a -s > analysis/complexity.txt
fi

# 2. cloc for language statistics
if command -v cloc &> /dev/null; then
  echo "Running line count by language..."
  cloc . --exclude-dir=node_modules,.git --md > analysis/language-stats.md
fi

# 3. SonarQube scanner (if configured)
if command -v sonar-scanner &> /dev/null; then
  echo "Running SonarQube scan..."
  sonar-scanner
fi

echo "Analysis complete. Results in ./analysis directory."
```

By integrating Recursivist with other tools, you can build comprehensive project documentation, analysis, and visualization pipelines that provide valuable insights into your codebase.
