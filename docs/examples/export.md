# Export Examples

This page provides practical examples of how to use Recursivist's export functionality to save directory structures in various formats.

## Basic Export Examples

### Exporting to Different Formats

#### Markdown Export

```bash
recursivist export --format md
```

This creates `structure.md` with a markdown representation of the directory structure.

#### JSON Export

```bash
recursivist export --format json
```

This creates `structure.json` with a JSON representation of the directory structure.

#### HTML Export

```bash
recursivist export --format html
```

This creates `structure.html` with an interactive HTML view of the directory structure.

#### Text Export

```bash
recursivist export --format txt
```

This creates `structure.txt` with a plain text ASCII tree representation.

#### React Component Export

```bash
recursivist export --format jsx
```

This creates `structure.jsx` with a React component for interactive visualization.

### Exporting to Multiple Formats Simultaneously

```bash
recursivist export --format "md json html"
```

This creates three files: `structure.md`, `structure.json`, and `structure.html`.

## Including File Statistics

### Exporting with Lines of Code Statistics

```bash
recursivist export --format md --sort-by-loc
```

This creates a markdown file with line counts for each file and directory:

```markdown
# 📂 my-project (4328 lines)

- 📁 **src** (3851 lines)
  - 📄 `main.py` (245 lines)
  - 📄 `utils.py` (157 lines)
  - 📁 **tests** (653 lines)
    - 📄 `test_main.py` (412 lines)
    - 📄 `test_utils.py` (241 lines)
- 📄 `README.md` (124 lines)
- 📄 `requirements.txt` (18 lines)
- 📄 `setup.py` (65 lines)
```

### Exporting with File Sizes

```bash
recursivist export --format html --sort-by-size
```

This creates an HTML file with file size information for each file and directory.

### Exporting with Modification Times

```bash
recursivist export --format json --sort-by-mtime
```

This creates a JSON file that includes modification timestamps for each file and directory.

### Combining Multiple Statistics

```bash
recursivist export --format txt --sort-by-loc --sort-by-size --sort-by-mtime
```

This combines lines of code, file sizes, and modification times in a single export.

## Customizing Export Output

### Custom Output Directory

```bash
recursivist export --format md --output-dir ./docs
```

This saves the markdown export to `./docs/structure.md`.

### Custom Filename Prefix

```bash
recursivist export --format json --prefix my-project
```

This creates `my-project.json` instead of `structure.json`.

### Combining Custom Directory and Filename

```bash
recursivist export --format html --output-dir ./documentation --prefix project-structure
```

This creates `./documentation/project-structure.html`.

## Filtered Exports

### Exporting with Directory Exclusions

```bash
recursivist export --format md --exclude "node_modules .git build"
```

This exports a markdown representation excluding the specified directories.

### Exporting with File Extension Exclusions

```bash
recursivist export --format json --exclude-ext ".pyc .log .tmp"
```

This exports a JSON representation excluding files with the specified extensions.

### Exporting with Pattern Exclusions

```bash
recursivist export --format html --exclude-pattern "*.test.js" "*.spec.js"
```

This exports an HTML representation excluding JavaScript test files.

### Exporting Only Specific Files

```bash
recursivist export --format md --include-pattern "src/**/*.js" "*.md"
```

This exports a markdown representation including only JavaScript files in the `src` directory and markdown files.

### Exporting with Gitignore Patterns

```bash
recursivist export --format txt --ignore-file .gitignore
```

This exports a text representation respecting the patterns in `.gitignore`.

## Depth-Limited Exports

### Exporting with Limited Depth

```bash
recursivist export --format html --depth 2
```

This exports an HTML representation limited to 2 levels of directory depth.

### Exporting Top-Level Overview

```bash
recursivist export --format md --depth 1
```

This exports a markdown representation showing only the top level of the directory structure.

## Full Path Exports

### JSON Export with Full Paths

```bash
recursivist export --format json --full-path
```

This exports a JSON representation with full file paths instead of just filenames.

### Markdown Export with Full Paths

```bash
recursivist export --format md --full-path
```

This exports a markdown representation with full file paths.

## Specific Project Exports

### Source Code Documentation with LOC Stats

```bash
recursivist export \
  --format md \
  --include-pattern "src/**/*" \
  --exclude-pattern "**/*.test.js" "**/*.spec.js" \
  --output-dir ./docs \
  --prefix source-structure \
  --sort-by-loc
```

This exports a markdown representation of the source code structure with lines of code information for documentation purposes.

### Project Overview for README

```bash
recursivist export \
  --format md \
  --depth 2 \
  --exclude "node_modules .git build dist" \
  --prefix project-overview \
  --sort-by-size
```

This creates a concise project overview with file size information suitable for inclusion in a README file.

## React Component Export Examples

### Basic React Component Export

```bash
recursivist export --format jsx --output-dir ./src/components
```

This exports a React component to `./src/components/structure.jsx`.

### Customized React Component with Statistics

```bash
recursivist export \
  --format jsx \
  --include-pattern "src/**/*" \
  --exclude "node_modules .git" \
  --output-dir ./src/components \
  --prefix project-explorer \
  --sort-by-loc \
  --sort-by-mtime
```

This exports a filtered React component focused on the source code to `./src/components/project-explorer.jsx` with lines of code and modification time information.

## Export for Different Use Cases

### Documentation Export with Stats

```bash
recursivist export \
  --format "md html" \
  --exclude "node_modules .git build dist" \
  --exclude-ext ".log .tmp .cache" \
  --output-dir ./docs \
  --prefix project-structure \
  --sort-by-loc
```

This exports both markdown and HTML representations with lines of code statistics for documentation purposes.

### Codebase Analysis Export

```bash
recursivist export \
  --format json \
  --full-path \
  --exclude "node_modules .git" \
  --prefix codebase-structure \
  --sort-by-loc \
  --sort-by-size
```

This exports a detailed JSON representation with full paths, line counts, and file sizes for codebase analysis.

### Website Integration Export

```bash
recursivist export \
  --format jsx \
  --exclude "node_modules .git build dist" \
  --output-dir ./website/src/components \
  --prefix directory-explorer \
  --sort-by-loc \
  --sort-by-mtime
```

This exports a React component with lines of code and modification time data for integration into a website.

## Batch Export Examples

### Multiple Export Configuration Script

Here's a shell script to export multiple configurations with statistics:

```bash
#!/bin/bash

# Export overview
recursivist export \
  --format md \
  --depth 2 \
  --exclude "node_modules .git" \
  --output-dir ./docs \
  --prefix project-overview \
  --sort-by-loc

# Export detailed structure
recursivist export \
  --format html \
  --exclude "node_modules .git" \
  --output-dir ./docs \
  --prefix detailed-structure \
  --sort-by-loc \
  --sort-by-size

# Export JSON for processing
recursivist export \
  --format json \
  --full-path \
  --output-dir ./data \
  --prefix directory-data \
  --sort-by-loc \
  --sort-by-size

# Export React component
recursivist export \
  --format jsx \
  --output-dir ./src/components \
  --prefix directory-viewer \
  --sort-by-loc \
  --sort-by-mtime
```

### Project Subdirectory Exports with Stats

Here's a script to export structures for each subdirectory with statistics:

```bash
#!/bin/bash

# Get all immediate subdirectories
for dir in */; do
  if [ -d "$dir" ] && [ "$dir" != "node_modules/" ] && [ "$dir" != ".git/" ]; then
    dir_name=$(basename "$dir")
    echo "Exporting structure for $dir_name..."

    recursivist export "$dir" \
      --format md \
      --output-dir ./docs/components \
      --prefix "$dir_name-structure" \
      --sort-by-loc \
      --sort-by-size
  fi
done
```

## Combining with Shell Commands

### Export and Process with jq

Export to JSON with LOC stats and process with jq to count files by type:

```bash
# Export with LOC stats
recursivist export --format json --prefix structure --sort-by-loc

# Use jq to analyze LOC data
jq -r '.structure | .. | objects | select(has("_files")) |
    ._files[] | select(type=="object" and has("loc")) |
    {ext: (.path | split(".") | .[-1]), loc: .loc} |
    .ext + "," + (.loc | tostring)' structure.json | \
  awk -F, '{sum[$1] += $2; count[$1]++}
    END {for (ext in sum)
      printf "%s files: %d lines in %d files (avg: %.1f lines/file)\n",
      ext, sum[$1], count[$1], sum[$1]/count[$1]}' | \
  sort -k2 -nr
```

### Export and Include in Documentation

```bash
# Export with LOC stats to markdown
recursivist export --format md --prefix structure --sort-by-loc

# Create README with project structure
echo "# Project Structure" > README.md
echo "" >> README.md
echo "## Directory Overview" >> README.md
echo "" >> README.md
cat structure.md >> README.md
```

This creates a README with the project structure including lines of code information.
