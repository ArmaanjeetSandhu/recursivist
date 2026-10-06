# Installation

Recursivist is published on PyPI and installs with `pip`.

## Requirements

- Python 3.10 or higher
- `pip` (or any compatible installer, such as [uv](https://docs.astral.sh/uv/))

Recursivist depends on [Rich](https://github.com/Textualize/rich) for terminal rendering, [Typer](https://github.com/fastapi/typer) for the command-line interface, [shellingham](https://github.com/sarugaku/shellingham) for shell detection, and [pathspec](https://pypi.org/project/pathspec/) for gitignore-style matching. These are installed automatically.

## Installing from PyPI

```bash
pip install recursivist
```

As a command-line tool, Recursivist can be installed in an isolated environment of its own with [pipx](https://pipx.pypa.io/) or [uv](https://docs.astral.sh/uv/), putting the `recursivist` command on your `PATH` without touching your other Python packages:

```bash
pipx install recursivist
# or
uv tool install recursivist
```

### Installing in a Virtual Environment

To keep the install isolated from system packages by hand, use a virtual environment:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
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

To work on Recursivist itself, follow the [Development Guide](../contributing/development.md), which also installs the development tools.

## Verifying the Installation

```bash
recursivist version
```

This prints the installed version, e.g. `Recursivist version: 2.1.0`.

## Short Alias

Installing Recursivist puts two commands on your `PATH`: `recursivist` and the shorter `rcv`. They are the same program under different names. Every command, option, and setting works identically whichever one you type:

```bash
recursivist visualize --depth 2
rcv visualize --depth 2
```

Help output and usage messages show whichever name you ran. [Shell completion](../user-guide/shell-completion.md#completion-for-the-alias) is set up per name. The rest of the documentation uses the full `recursivist` name.

## Nerd Font Icons (Optional)

By default Recursivist labels files and directories with generic emoji (📄 for files, 📂 for directories with contents, 📁 for empty ones), which render everywhere. It can also use file-type-specific [Nerd Font](https://www.nerdfonts.com/) glyphs, which require a patched font installed and selected in your terminal. To switch styles:

```bash
recursivist config set icon-style nerd
```

See [Icon Styles](../user-guide/visualization.md#icon-styles) for details. If glyphs appear as boxes or question marks, your terminal font is not a Nerd Font; switch back with `recursivist config set icon-style emoji`.

## Terminal Compatibility

For the best experience, use a terminal with Unicode and ANSI color support. On Windows, [Windows Terminal](https://aka.ms/terminal) is recommended.

## Next Steps

Continue to the [Quick Start Guide](quick-start.md) to start visualizing directory structures.
