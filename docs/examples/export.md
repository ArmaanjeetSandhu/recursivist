# Export Examples

This page provides practical examples of how to use Recursivist's export functionality to save directory structures in various formats.

## Basic Export Examples

### Exporting to Different Formats

#### Markdown Export

```bash
recursivist export \
--format md
```

This creates `structure.md` with a markdown representation of the directory structure.

#### JSON Export

```bash
recursivist export \
--format json
```

This creates `structure.json` with a JSON representation of the directory structure.

#### HTML Export

```bash
recursivist export \
--format html
```

This creates `structure.html` with an interactive HTML view of the directory structure.

#### Text Export

```bash
recursivist export \
--format txt
```

This creates `structure.txt` with a plain text ASCII tree representation.

#### React Component Export

```bash
recursivist export \
--format jsx
```

This creates `structure.jsx` with a React component for interactive visualization.

### Exporting to Multiple Formats Simultaneously

```bash
recursivist export \
--format "md json html"
```

This creates three files: `structure.md`, `structure.json`, and `structure.html`.

## Customizing Export Output

### Custom Output Directory

```bash
recursivist export \
--format md \
--output-dir ./docs
```

This saves the markdown export to `./docs/structure.md`.

### Custom Filename Prefix

```bash
recursivist export \
--format json \
--prefix my-project
```

This creates `my-project.json` instead of `structure.json`.

### Combining Custom Directory and Filename

```bash
recursivist export \
--format html \
--output-dir ./documentation \
--prefix project-structure
```

This creates `./documentation/project-structure.html`.

## Filtered Exports

### Exporting with Directory Exclusions

```bash
recursivist export \
--format md \
--exclude "node_modules .git build"
```

This exports a markdown representation excluding the specified directories.

### Exporting with File Extension Exclusions

```bash
recursivist export \
--format json \
--exclude-ext ".pyc .log .tmp"
```

This exports a JSON representation excluding files with the specified extensions.

### Exporting with Pattern Exclusions

```bash
recursivist export \
--format html \
--exclude-pattern "*.test.js" "*.spec.js"
```

This exports an HTML representation excluding JavaScript test files.

### Exporting Only Specific Files

```bash
recursivist export \
--format md \
--include-pattern "src/**/*.js" "*.md"
```

This exports a markdown representation including only JavaScript files in the `src` directory and markdown files.

### Exporting with Gitignore Patterns

```bash
recursivist export \
--format txt \
--ignore-file .gitignore
```

This exports a text representation respecting the patterns in `.gitignore`.

## Depth-Limited Exports

### Exporting with Limited Depth

```bash
recursivist export \
--format html \
--depth 2
```

This exports an HTML representation limited to 2 levels of directory depth.

### Exporting Top-Level Overview

```bash
recursivist export \
--format md \
--depth 1
```

This exports a markdown representation showing only the top level of the directory structure.

## Full Path Exports

### JSON Export with Full Paths

```bash
recursivist export \
--format json \
--full-path
```

This exports a JSON representation with full file paths instead of just filenames.

### Markdown Export with Full Paths

```bash
recursivist export \
--format md \
--full-path
```

This exports a markdown representation with full file paths.

## Specific Project Exports

### Source Code Documentation

```bash
recursivist export \
--format md \
--include-pattern "src/**/*" \
--exclude-pattern "**/*.test.js" "**/*.spec.js" \
--output-dir ./docs \
--prefix source-structure
```

This exports a markdown representation of the source code structure for documentation purposes.

### Project Overview for README

```bash
recursivist export \
--format md \
--depth 2 \
--exclude "node_modules .git build dist" \
--prefix project-overview
```

This creates a concise project overview suitable for inclusion in a README file.

## React Component Export Examples

### Basic React Component Export

```bash
recursivist export \
--format jsx \
--output-dir ./src/components
```

This exports a React component to `./src/components/structure.jsx`.

### Customized React Component

```bash
recursivist export \
--format jsx \
--include-pattern "src/**/*" \
--exclude "node_modules .git" \
--output-dir ./src/components \
--prefix project-explorer
```

This exports a filtered React component focused on the source code to `./src/components/project-explorer.jsx`.

## Export for Different Use Cases

### Documentation Export

```bash
recursivist export \
--format "md html" \
--exclude "node_modules .git build dist" \
--exclude-ext ".log .tmp .cache" \
--output-dir ./docs \
--prefix project-structure
```

This exports both markdown and HTML representations for documentation purposes.

### Codebase Analysis Export

```bash
recursivist export \
--format json \
--full-path \
--exclude "node_modules .git" \
--prefix codebase-structure
```

This exports a detailed JSON representation with full paths for codebase analysis.

### Website Integration Export

```bash
recursivist export \
--format jsx \
--exclude "node_modules .git build dist" \
--output-dir ./website/src/components \
--prefix directory-explorer
```

This exports a React component for integration into a website.

## Batch Export Examples

### Multiple Export Configuration Script

Here's a shell script to export multiple configurations:

```bash
#!/bin/bash

# Export overview
recursivist export \
--format md \
--depth 2 \
--exclude "node_modules .git" \
--output-dir ./docs \
--prefix project-overview

# Export detailed structure
recursivist export \
--format html \
--exclude "node_modules .git" \
--output-dir ./docs \
--prefix detailed-structure

# Export JSON for processing
recursivist export \
--format json \
--full-path \
--output-dir ./data \
--prefix directory-data

# Export React component
recursivist export \
--format jsx \
--output-dir ./src/components \
--prefix directory-viewer
```

### Project Subdirectory Exports

Here's a script to export structures for each subdirectory:

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
    --prefix "$dir_name-structure"
  fi
done
```

## Combining with Shell Commands

### Export and Process with jq

Export to JSON and process with jq to count files by type:

```bash
recursivist export \
--format json \
--prefix structure
jq '.structure | .. | objects | select(has("_files")) | ._files | length' structure.json | jq -s 'add'
```

This exports the structure to JSON and then uses jq to count the total number of files.

### Export and Include in Documentation

```bash
recursivist export \
--format md \
--prefix structure
echo "# Project Structure" > README.md
echo "" >> README.md
cat structure.md >> README.md
```

This exports the structure to markdown and then includes it in the README.
