# Installation

Recursivist is available on PyPI and can be installed with pip, the Python package manager.

## Requirements

- Python 3.7 or higher
- pip (Python package manager)

## Installing from PyPI

The recommended way to install Recursivist is through PyPI:

```bash
pip install recursivist
```

This will install Recursivist and all of its dependencies, including:

- [Rich](https://github.com/Textualize/rich) - For beautiful terminal formatting
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

## Next Steps

Now that you have Recursivist installed, check out the [Quick Start Guide](quick-start.md) to begin visualizing directory structures.
