# Installation

Recursivist is published on PyPI and installs with `pip`.

## Requirements

- Python 3.10 or higher
- `pip` (or any compatible installer, such as [uv](https://docs.astral.sh/uv/))

Recursivist depends on [Rich](https://github.com/Textualize/rich) for terminal rendering, [Typer](https://github.com/fastapi/typer) for the command-line interface, and [shellingham](https://github.com/sarugaku/shellingham) for shell detection. These are installed automatically.

## Installing from PyPI

```bash
pip install recursivist
```

## Installing from Source

To get the latest unreleased changes, install from the repository:

```bash
git clone https://github.com/ArmaanjeetSandhu/recursivist.git
cd recursivist
pip install -e .
```

The `-e` flag installs the package in editable mode, so changes to the source are reflected without reinstalling.

To also install the development tools (pytest, Ruff, mypy, pyright, nox, and others), add the `dev` extra:

```bash
pip install -e ".[dev]"
```

## Verifying the Installation

```bash
recursivist version
```

This prints the installed version, e.g. `Recursivist version: 2.1.0`.

## Nerd Font Icons (Optional)

By default Recursivist labels files and directories with two generic emoji (📄 and 📁), which render everywhere. It can also use file-type-specific [Nerd Font](https://www.nerdfonts.com/) glyphs, which require a patched font installed and selected in your terminal. To switch styles:

```bash
recursivist config set icon-style nerd
```

See [Basic Usage](../user-guide/basic-usage.md#icon-styles) for details. If glyphs appear as boxes or question marks, your terminal font is not a Nerd Font; switch back with `recursivist config set icon-style emoji`.

## Terminal Compatibility

For the best experience, use a terminal with Unicode and ANSI color support. On Windows, [Windows Terminal](https://aka.ms/terminal) is recommended. A virtual environment keeps the install isolated from system packages:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
pip install recursivist
```

## Next Steps

Continue to the [Quick Start Guide](quick-start.md) to start visualizing directory structures.
