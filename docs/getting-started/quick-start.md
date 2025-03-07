# Quick Start Guide

This guide will help you quickly get started with Recursivist, a beautiful directory structure visualization tool.

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

### Export a Directory Structure

To export the current directory structure to Markdown format:

```bash
recursivist export \
--format md
```

This will create a file named `structure.md` in the current directory.

### Compare Two Directories

To compare two directory structures side by side:

```bash
recursivist compare dir1 dir2
```

This will display both directory trees with highlighted differences.

## Common Options

Here are some common options that you can use with Recursivist commands:

### Exclude Directories

To exclude specific directories (like `node_modules` or `.git`):

```bash
recursivist visualize \
--exclude "node_modules .git"
```

### Exclude File Extensions

To exclude files with specific extensions (like `.pyc` or `.log`):

```bash
recursivist visualize \
--exclude-ext ".pyc .log"
```

### Limit Directory Depth

To limit the depth of the directory tree (useful for large projects):

```bash
recursivist visualize \
--depth 3
```

### Show Full Paths

To show full paths instead of just filenames:

```bash
recursivist visualize \
--full-path
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

### Export to Multiple Formats

```bash
recursivist export \
--format "txt md json" \
--output-dir ./exports
```

This exports the directory structure to text, markdown, and JSON formats in the `./exports` directory.

### Compare with Exclusions

```bash
recursivist compare dir1 dir2 \
--exclude node_modules \
--exclude-ext .pyc
```

This compares two directories while ignoring `node_modules` directories and `.pyc` files.

## Next Steps

- Learn more about [visualization options](../user-guide/visualization.md)
- Explore [pattern filtering](../user-guide/pattern-filtering.md) for precise control
- Check out the various [export formats](../reference/export-formats.md)
- See the complete [CLI reference](../reference/cli-reference.md) for all available options
