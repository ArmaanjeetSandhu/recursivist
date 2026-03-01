# Installation

Recursivist is available on PyPI and can be installed with pip, the Python package manager.

## Requirements

- Python 3.9 or higher
- pip (Python package manager)

## Installing from PyPI

The recommended way to install Recursivist is through PyPI:

```bash
pip install recursivist
```

This will install Recursivist and all of its dependencies, including:

- [Rich](https://github.com/Textualize/rich) - For beautiful terminal formatting and colored output
- [Typer](https://github.com/tiangolo/typer) - For the intuitive CLI interface

## Installing from Source

For the latest development version or if you want to contribute to the project, you can install Recursivist directly from the source code:

```bash
git clone https://github.com/ArmaanjeetSandhu/recursivist.git
cd recursivist
pip install -e .
```

The `-e` flag installs the package in "editable" mode, which means changes to the source code will be reflected in the installed package without needing to reinstall.

## Installing for Development

If you plan to contribute to Recursivist, you should install the development dependencies:

```bash
git clone https://github.com/ArmaanjeetSandhu/recursivist.git
cd recursivist
pip install -e ".[dev]"
```

This installs Recursivist along with all the development tools, such as pytest for testing.

## Verifying Installation

After installation, you can verify that Recursivist was installed correctly by checking its version:

```bash
recursivist version
```

You should see the current version of Recursivist displayed.

## System-specific Notes

### Windows

On Windows, it's recommended to use a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install recursivist
```

For the best experience on Windows, use a terminal that supports Unicode and ANSI colors, such as Windows Terminal.

### macOS

On macOS, if you're using Homebrew's Python, you might need to use:

```bash
python3 -m pip install recursivist
```

### Linux

On Linux, you might need to install Python development headers first:

```bash
# Debian-based systems (Ubuntu, etc.)
sudo apt-get install python3-dev

# Red Hat-based systems (Fedora, CentOS, etc.)
sudo dnf install python3-devel

# Then install Recursivist
pip3 install recursivist
```

## Troubleshooting Installation Issues

### Unicode Display Problems

If you see squares or question marks instead of emoji icons in the output:

1. Ensure your terminal supports Unicode
2. Check that you're using a font that includes emoji characters
3. On Windows, make sure you're using Windows Terminal or another modern terminal

### Color Display Issues

If colors aren't displaying correctly:

1. Ensure your terminal supports ANSI colors
2. Check if you need to enable color support in your terminal settings
3. Try running with the `TERM=xterm-256color` environment variable

### Missing Dependencies

If you encounter missing dependency errors:

```bash
# Try reinstalling with the --force-reinstall flag
pip install --force-reinstall recursivist

# Or specify the dependencies explicitly
pip install rich typer
```

## Next Steps

Now that you have Recursivist installed, check out the [Quick Start Guide](quick-start.md) to begin visualizing directory structures.
