# Recursivist

A beautiful command-line tool for visualizing directory structures with rich formatting, color-coding, and multiple export options.

## Key Features

- 🎨 **Colorful Visualization**: Each file type is assigned a unique color for easy identification
- 🌳 **Tree Structure**: Displays your directories in an intuitive, hierarchical tree format
- 📁 **Smart Filtering**: Easily exclude directories and file extensions you don't want to see
- 🧩 **Gitignore Support**: Automatically respects your `.gitignore` patterns
- 🔄 **Directory Comparison**: Compare two directory structures side by side with highlighted differences
- 📊 **Multiple Export Formats**: Export to TXT, rST, Markdown, HTML, JSON, and SVG

## Installation

```bash
pip install recursivist
```

## Quick Start

Just run the command in any directory to see a beautifully formatted directory tree:

```bash
recursivist visualize
```

For a specific directory:

```bash
recursivist visualize /path/to/directory
```

To exclude common directories:

```bash
recursivist visualize \
--exclude node_modules --exclude .git
```

To export the structure to markdown:

```bash
recursivist export \
--format md
```

To compare two directories:

```bash
recursivist compare dir1 dir2
```

## Documentation

For comprehensive documentation, including detailed usage instructions, examples, and API reference, click [here](https://armaanjeetsandhu.github.io/recursivist/).
