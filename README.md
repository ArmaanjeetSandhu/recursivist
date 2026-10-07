<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/ArmaanjeetSandhu/recursivist/main/docs/assets/images/logo-white.svg">
  <img src="https://raw.githubusercontent.com/ArmaanjeetSandhu/recursivist/main/docs/assets/images/logo-black.svg" alt="Recursivist logo" width="88">
</picture>

# Recursivist

**See the shape of any codebase in one command**

[![PyPI](https://img.shields.io/pypi/v/recursivist?color=blue&style=for-the-badge)](https://pypi.org/project/recursivist/)
[![Python](https://img.shields.io/pypi/pyversions/recursivist?style=for-the-badge)](https://pypi.org/project/recursivist/)
[![Tests](https://img.shields.io/github/actions/workflow/status/ArmaanjeetSandhu/recursivist/test.yml?branch=main&label=tests&style=for-the-badge)](https://github.com/ArmaanjeetSandhu/recursivist/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/sonar/coverage/ArmaanjeetSandhu_recursivist?server=https%3A%2F%2Fsonarcloud.io&style=for-the-badge)](https://sonarcloud.io/summary/new_code?id=ArmaanjeetSandhu_recursivist)
[![Quality Gate Status](https://img.shields.io/sonar/quality_gate/ArmaanjeetSandhu_recursivist?server=https%3A%2F%2Fsonarcloud.io&style=for-the-badge)](https://sonarcloud.io/summary/new_code?id=ArmaanjeetSandhu_recursivist)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](https://github.com/ArmaanjeetSandhu/recursivist/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-online-8A2BE2?style=for-the-badge)](https://armaanjeetsandhu.github.io/recursivist/)

</div>

## Installation

```bash
pip install recursivist
```

Prefer an isolated install? `pipx install recursivist` and `uv tool install recursivist` both work.

## Key Features

- 🎨 **Colorful Visualization**: Each file type is assigned a unique color for easy identification
- 🌳 **Tree Structure**: Displays your directories in an intuitive, hierarchical tree format
- 📁 **Smart Filtering**: Easily exclude directories and file extensions you don't want to see
- 🧩 **Gitignore Support**: Automatically respects your `.gitignore` patterns
- 🔄 **Directory Comparison**: Compare two directory structures side by side with highlighted differences
- 📊 **Multiple Export Formats**: Export to TXT, rST, Markdown, HTML, JSON, and SVG

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
recursivist visualize --exclude node_modules --exclude .git
```

To export the structure to markdown:

```bash
recursivist export --format md
```

To compare two directories:

```bash
recursivist compare dir1 dir2
```

## Documentation

For comprehensive documentation, including detailed usage instructions, examples, and API reference, click [here](https://armaanjeetsandhu.github.io/recursivist/).
