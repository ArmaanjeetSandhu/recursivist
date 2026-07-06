# Development Guide

This guide is for developers who want to contribute to or extend Recursivist.

## Setting Up a Development Environment

### Prerequisites

- Python 3.10 or higher
- Git
- Optionally [uv](https://docs.astral.sh/uv/) for fast environment and dependency management

### Clone and Install

```bash
git clone https://github.com/ArmaanjeetSandhu/recursivist.git
cd recursivist

# Create and activate a virtual environment (uv shown; venv works too)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
uv pip install -e ".[dev]"
```

Editable mode means source changes take effect without reinstalling.

### Install Pre-commit Hooks

```bash
pre-commit install
```

The hooks run Ruff (lint and format) and the type checkers on every commit.

## Project Structure

Recursivist is organized into small, focused modules:

```
recursivist/
├── __init__.py        # Package metadata and version
├── __main__.py        # `python -m recursivist` entry point
├── _models.py         # FileEntry (a NamedTuple), FileEntry.from_raw and .coerce
├── cli.py             # Typer-based command-line interface
├── flags.py           # DisplayOptions and command-line-order flag resolution
├── scanner.py         # Directory traversal -> nested structure dict
├── tree.py            # Rich tree rendering (build_tree, display_tree)
├── compare.py         # Side-by-side comparison and rendering
├── filtering.py       # should_exclude, compile_regex_patterns, parse_ignore_file
├── sorting.py         # sort_files_by_type, sort_files_by_similarity
├── metrics.py         # Lines of code, size, mtime, and formatting
├── colors.py          # generate_color_for_extension
├── icons.py           # get_icon (emoji and Nerd Font)
├── git_status.py      # get_git_status
├── config.py          # load_config, save_config, get_config_path
└── exporters/
    ├── __init__.py    # get_exporter factory and the _EXPORTERS registry
    ├── base.py        # BaseExporter
    ├── txt.py         # TxtExporter
    ├── json.py        # JsonExporter
    ├── html.py        # HtmlExporter
    ├── markdown.py    # MarkdownExporter
    ├── jsx.py         # JsxExporter
    ├── svg.py         # SvgExporter
    └── rst.py         # RstExporter
```

See the [API Reference](../reference/api-reference.md) for the public functions of each module.

## Development Workflow

1. Create a branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes.
3. Run the test suite:

   ```bash
   nox -s tests
   ```

4. Commit (pre-commit hooks run automatically):

   ```bash
   git add .
   git commit -m "Describe your change"
   ```

5. Push and open a pull request.

## Code Style and Checks

Recursivist uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, and both mypy (strict) and pyright for type checking. The Nox sessions wrap these:

```bash
nox -s lint        # Ruff check + format
nox -s typecheck   # mypy and pyright
nox -s tests       # pytest across supported Python versions
nox -s docs        # build the documentation
```

You can also run the tools directly:

```bash
ruff check --fix .
ruff format .
```

## Extending Recursivist

### Add a New Command

Add a Typer command in `cli.py` and delegate to the appropriate module:

```python
@app.command()
def your_command(
    directory: Path = typer.Argument(".", help="Directory path to process"),
):
    """One-line summary shown in --help.

    A longer description with usage details.
    """
    ...
```

Implement the underlying logic in a focused module (or a new one), and add tests.

### Add a New Export Format

Exporters live in `recursivist/exporters/` and subclass `BaseExporter`, which stores the structure and display options and defines the `export(output_path)` method to override.

1. Create `recursivist/exporters/your_format.py`:

   ```python
   from .base import BaseExporter


   class YourFormatExporter(BaseExporter):
       def export(self, output_path: str) -> None:
           with open(output_path, "w", encoding="utf-8") as f:
               # Build output from self.structure and self.root_name,
               # honoring the resolved display options exposed by BaseExporter:
               # self.sort_key, self.metrics (ordered), self.show_git_status,
               # self.icon_style, and self.show_full_path as appropriate.
               ...
   ```

2. Register it in `recursivist/exporters/__init__.py` by importing the class and adding it to the `_EXPORTERS` map:

   ```python
   from .your_format import YourFormatExporter

   _EXPORTERS = {
       # existing entries...
       "your_format": YourFormatExporter,
   }
   ```

3. Add the format to the `--format` option in `cli.py` and add tests.

### Add a New File Statistic

To add a metric beyond lines of code, size, and mtime:

1. Collect it in `get_directory_structure` (`scanner.py`) and add a flag to enable it.
2. Thread it through `FileEntry` in `_models.py` and the formatting helpers in `metrics.py`.
3. Register the metric and its flags in `flags.py` so they resolve into `DisplayOptions` (a sorting flag, a display-only flag, or both).
4. Surface it in `build_tree` (`tree.py`), the exporters, and `compare.py`.
5. Add the CLI options in `cli.py` and wire them into `resolve_display_options`.

### Extend Pattern Matching

Pattern logic lives in `filtering.py`. To support a new pattern type, extend `should_exclude`, add a flag in `cli.py`, document it, and add tests.

### Customize Colorization

Per-extension colors come from `generate_color_for_extension` in `colors.py`. To give common extensions fixed colors, add a lookup table and consult it before falling back to the derived color:

```python
EXTENSION_COLORS = {
    ".py": "#3776AB",
    ".js": "#F7DF1E",
    ".html": "#E34C26",
}
```

## Debugging

Run any command with `--verbose` for DEBUG-level logging:

```bash
recursivist visualize --verbose
```

Use the built-in `breakpoint()` to drop into the debugger, or set breakpoints in your IDE.

## Documentation

Use Google-style docstrings for public functions, classes, and methods — the [API Reference](../reference/api-reference.md) is generated from them via mkdocstrings. Build the docs locally with:

```bash
nox -s docs
```

Keep command help text in `cli.py` in sync when you add or change options.

## Release Process

Recursivist follows [Semantic Versioning](https://semver.org/): MAJOR for incompatible API changes, MINOR for backwards-compatible features, PATCH for backwards-compatible fixes.

1. Update the version in `pyproject.toml`.
2. Commit and push to `main`. The `tag-release` workflow detects the version change and creates and pushes the matching Git tag automatically.
3. Maintainers build and upload to PyPI:

   ```bash
   python -m build
   twine upload dist/*
   ```

## Performance Notes

For large directory trees: filter early (exclude heavy directories), be mindful that `--sort-by-loc` reads every file, and profile hotspots with `cProfile` when needed:

```python
import cProfile, pstats

cProfile.run("your_function_call()", "profile_results")
pstats.Stats("profile_results").sort_stats("cumulative").print_stats(20)
```
