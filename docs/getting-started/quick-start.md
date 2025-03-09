# Quick Start Guide

This guide will help you quickly get started with Recursivist, a powerful directory structure visualization tool.

## Basic Commands

After [installing Recursivist](installation.md), you can start using it right away. Here are the basic commands:

### Visualize a Directory

To visualize the current directory structure:

```bash
recursivist visualize
```

This will display a colorful tree representation of the current directory in your terminal.

To visualize a specific directory:

```bash
recursivist visualize /path/to/your/directory
```

### Display File Statistics

Recursivist can show and sort by various file statistics:

```bash
# Show lines of code
recursivist visualize --sort-by-loc

# Show file sizes
recursivist visualize --sort-by-size

# Show modification times
recursivist visualize --sort-by-mtime

# Combine multiple statistics
recursivist visualize --sort-by-loc --sort-by-size
```

### Export a Directory Structure

To export the current directory structure to various formats:

```bash
# Export to Markdown
recursivist export --format md

# Export to HTML
recursivist export --format html

# Export to JSON
recursivist export --format json

# Export to plain text
recursivist export --format txt

# Export to React component
recursivist export --format jsx
```

### Compare Two Directories

To compare two directory structures side by side:

```bash
recursivist compare dir1 dir2
```

This will display both directory trees with highlighted differences.

To save the comparison as an HTML file:

```bash
recursivist compare dir1 dir2 --save
```

## Common Options

Here are some common options that you can use with Recursivist commands:

### Exclude Directories

To exclude specific directories (like `node_modules` or `.git`):

```bash
recursivist visualize --exclude "node_modules .git"
```

### Exclude File Extensions

To exclude files with specific extensions (like `.pyc` or `.log`):

```bash
recursivist visualize --exclude-ext ".pyc .log"
```

### Pattern Filtering

To exclude files matching specific patterns:

```bash
# Using glob patterns (default)
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"

# Using regular expressions
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex
```

To include only specific files:

```bash
recursivist visualize --include-pattern "src/**/*.js" "*.md"
```

### Limit Directory Depth

To limit the depth of the directory tree (useful for large projects):

```bash
recursivist visualize --depth 3
```

### Show Full Paths

To show full paths instead of just filenames:

```bash
recursivist visualize --full-path
```

## Quick Examples

### Basic Directory Visualization

```bash
recursivist visualize
```

This will produce output similar to:

```
📂 my-project
├── 📁 src
│   ├── 📄 main.py
│   ├── 📄 utils.py
│   └── 📁 tests
│       ├── 📄 test_main.py
│       └── 📄 test_utils.py
├── 📄 README.md
├── 📄 requirements.txt
└── 📄 setup.py
```

### Visualizing with File Statistics

```bash
recursivist visualize --sort-by-loc
```

Output:

```
📂 my-project (4328 lines)
├── 📁 src (3851 lines)
│   ├── 📄 main.py (245 lines)
│   ├── 📄 utils.py (157 lines)
│   └── 📁 tests (653 lines)
│       ├── 📄 test_main.py (412 lines)
│       └── 📄 test_utils.py (241 lines)
├── 📄 README.md (124 lines)
├── 📄 requirements.txt (18 lines)
└── 📄 setup.py (65 lines)
```

### Export to Multiple Formats

```bash
recursivist export \
--format "txt md json" \
--output-dir ./exports \
--prefix project-structure
```

This exports the directory structure to text, markdown, and JSON formats in the `./exports` directory.

### Compare with Exclusions

```bash
recursivist compare dir1 dir2 \
--exclude node_modules \
--exclude-ext .pyc
```

This compares two directories while ignoring `node_modules` directories and `.pyc` files.

### Compare with File Statistics

```bash
recursivist compare dir1 dir2 --sort-by-size
```

This compares two directories with file sizes displayed, making it easy to see size differences between the two directories.

## Shell Completion

Generate shell completion scripts for easier command usage:

```bash
# For Bash
recursivist completion bash > ~/.bash_completion.d/recursivist
source ~/.bash_completion.d/recursivist

# For Zsh, Fish, or PowerShell
recursivist completion zsh|fish|powershell
```

## Next Steps

- Learn more about [visualization options](../user-guide/visualization.md)
- Explore [pattern filtering](../user-guide/pattern-filtering.md) for precise control
- Check out the various [export formats](../reference/export-formats.md)
- See the complete [CLI reference](../reference/cli-reference.md) for all available options
- Discover [advanced examples](../examples/advanced.md) for sophisticated usage patterns
