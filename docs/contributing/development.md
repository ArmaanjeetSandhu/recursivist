# Development Guide

This guide is for developers who want to contribute to or extend Recursivist. For the contribution workflow itself — branches, commits, and pull requests — see [Contributing](index.md).

## Setting Up a Development Environment

### Prerequisites

- Python 3.10 or higher
- Git
- [uv](https://docs.astral.sh/uv/), which the Nox sessions and the pre-commit hooks use to manage environments:

    ```bash
    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

### Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/recursivist.git
cd recursivist

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
uv pip install -e ".[dev]"
```

Editable mode means source changes take effect without reinstalling. Check that the CLI runs from your checkout:

```bash
python -m recursivist --help
```

### Install Pre-commit Hooks

```bash
uv pip install pre-commit
pre-commit install
```

The hooks run Ruff (lint and format) and the type checkers on every commit, along with a few file hygiene checks.

## Project Structure

Recursivist is organized into small, focused modules:

```
recursivist/
├── __init__.py        # Package metadata and version
├── __main__.py        # `python -m recursivist` entry point
├── _models.py         # Directory (a dataclass) and FileEntry (a NamedTuple)
├── cli.py             # Typer-based command-line interface
├── flags.py           # DisplayOptions and command-line-order flag resolution
├── scanner.py         # Directory traversal -> tree of Directory nodes
├── tree.py            # Rich tree rendering (build_tree, display_tree)
├── compare.py         # Side-by-side comparison and rendering
├── filtering.py       # should_exclude, compile_regex_patterns, parse_ignore_file
├── sorting.py         # sort_files_by_type, sort_files_by_similarity
├── metrics.py         # Lines of code, size, mtime, and formatting
├── colors.py          # build_color_map, ensure_contrast
├── icons.py           # get_icon (emoji and Nerd Font)
├── git_status.py      # get_git_status
├── github.py          # parse_github_url, checkout_repository, apply_github_urls
├── config.py          # User preferences and project configuration
└── exporters/
    ├── __init__.py    # get_exporter factory and the _EXPORTERS registry
    ├── base.py        # BaseExporter
    ├── txt.py         # TxtExporter
    ├── json.py        # JsonExporter
    ├── html.py        # HtmlExporter
    ├── markdown.py    # MarkdownExporter
    ├── svg.py         # SvgExporter
    └── rst.py         # RstExporter
```

See the [Python API reference](../reference/api-reference.md) for the public functions of each module.

## Running the Checks

[Nox](https://nox.thea.codes/) is the task runner. Every session runs in its own uv-managed virtual environment:

| Session            | What it runs                                                           |
| ------------------ | ---------------------------------------------------------------------- |
| `nox -s lint`      | `ruff check` and `ruff format --check`                                 |
| `nox -s typecheck` | `mypy --strict` and `pyright`                                          |
| `nox -s tests`     | pytest on every supported Python version (3.10–3.14)                   |
| `nox -s docs`      | A strict build of the documentation, which fails on a broken reference |

Running `nox` with no arguments runs `lint`, `typecheck`, and `tests`. Arguments after `--` are passed through to pytest; see the [Testing Guide](testing.md).

## Coding Standards

### Code Style

Recursivist uses [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting. `nox -s lint` only checks; to fix and reformat in place, run the tool directly:

```bash
ruff check --fix .
ruff format .
```

Ruff also runs automatically from the pre-commit hooks.

### Type Annotations

All code must pass both **mypy** (strict mode) and **pyright**. Use standard type hints:

```python
def process_data(
    data: dict[str, list[str]],
    options: set[str] | None = None,
) -> bool:
    return True
```

### Docstrings

Write docstrings for all public modules, functions, classes, and methods, in the Google style used by the existing code — the [Python API reference](../reference/api-reference.md) is generated from them via mkdocstrings.

```python
def function(arg1: str, arg2: int) -> bool:
    """A short description of the function.

    A more detailed description explaining the behavior, edge cases,
    and implementation details if relevant.

    Args:
        arg1: Description of the first argument
        arg2: Description of the second argument

    Returns:
        Description of the return value

    Raises:
        ValueError: When the input is invalid
    """
```

!!! note "Command docstrings are help text"

    The docstring of a CLI command in `recursivist/cli.py` is printed as that command's `--help` text, exactly as written, so it does not follow the example above. Keep it to what a user of the command needs: leave out the `Args:`, `Returns:`, and `Raises:` sections, and name flags (`--exclude`) rather than parameters (`exclude_dirs`). Wrap the paragraphs after the first at 76 characters, not counting indentation, so that they fit an 80-column terminal. Rich reads a lowercase word in square brackets as markup and drops it, so avoid text such as `[tool.recursivist]`.

## Working on the Documentation

The documentation lives in `docs/` and is built with [Zensical](https://zensical.org/); the navigation is defined in `zensical.toml`. Install the documentation dependencies and start a live preview:

```bash
uv pip install -e ".[docs]"
zensical serve
```

Before opening a pull request, run the same strict build that CI runs:

```bash
nox -s docs
```

When you add or change a command-line option, update its help text in `cli.py`, the [CLI Reference](../reference/cli-reference.md), and the guide page that explains it. Each topic is explained in one place and linked from the others, so prefer a link over a second explanation.

Show terminal output as a static terminal illustration — the `terminal-demo` markup used on the home page and throughout the guide, without the command line that triggers the typing animation — rather than as a plain code block or an image. Add the `compact` class for output wider than 64 columns, so that it keeps the same margin on the right as on the left. For boxed output such as the `compare` panels, draw the boxes with the `terminal-panel` classes rather than with box-drawing characters, which leave gaps between lines. Contents of exported files stay in ordinary code blocks.

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

3. Add the format to the `--format` option in `cli.py`, document it in [Export Formats](../reference/export-formats.md), and add tests.

### Add a New File Statistic

To add a metric beyond lines of code, size, and mtime:

1. Collect it in `get_directory_structure` (`scanner.py`) and add a flag to enable it.
2. Thread it through `FileEntry` and `Directory` in `_models.py` and the formatting helpers in `metrics.py`.
3. Register the metric and its flags in `flags.py` so they resolve into `DisplayOptions` (a sorting flag, a display-only flag, or both).
4. Surface it in `build_tree` (`tree.py`), the exporters, and `compare.py`.
5. Add the CLI options in `cli.py`, giving each a `_records_order` callback with its flag id, and wire them into `resolve_display_options`.

### Extend Pattern Matching

Pattern logic lives in `filtering.py`. To support a new pattern type, extend `should_exclude`, add a flag in `cli.py`, document it, and add tests.

### Customize Rendering or Colorization

Custom rendering builds on `build_tree` and `display_tree` in `tree.py`, which both render a scanned `Directory`.

Per-extension colors come from `build_color_map` in `colors.py`, which colors the extensions found in a tree in sorted order so that the same set of extensions always yields the same mapping. To give common extensions fixed colors, add a lookup table and consult it before falling back to the derived color:

```python
EXTENSION_COLORS = {
    ".py": "#3776AB",
    ".js": "#F7DF1E",
    ".html": "#E34C26",
}
```

These colors are tuned for a dark terminal background. Renderers that draw onto a known background pass them through `ensure_contrast` in `colors.py` first, which darkens or lightens a color (preserving its hue) until it meets a WCAG contrast ratio. The HTML exporter holds every color it emits to `WCAG_AAA_NORMAL_TEXT` (7:1), so a custom palette stays accessible without needing to be hand-checked.

## Debugging

Run any command with `--verbose` for DEBUG-level logging:

```bash
recursivist visualize --verbose
```

Use the built-in `breakpoint()` to drop into the debugger, or set breakpoints in your IDE.

## Performance Notes

For large directory trees: filter early (exclude heavy directories), be mindful that `--sort-by-loc` reads every file, and profile hotspots with `cProfile` when needed:

```python
import cProfile, pstats

cProfile.run("your_function_call()", "profile_results")
pstats.Stats("profile_results").sort_stats("cumulative").print_stats(20)
```

## Release Process

Recursivist follows [Semantic Versioning](https://semver.org/): MAJOR for incompatible API changes, MINOR for backwards-compatible features, PATCH for backwards-compatible fixes. Releases are largely automated via GitHub Actions.

1. **Bump the version** in both places it is recorded: `version` in `pyproject.toml`, which names the release, and `__version__` in `recursivist/__init__.py`, which `recursivist version` prints.

    ```toml
    version = "X.Y.Z"
    ```

    ```python
    __version__ = "X.Y.Z"
    ```

2. **Commit and push to `main`**:

    ```bash
    git add pyproject.toml recursivist/__init__.py
    git commit -m "Release vX.Y.Z"
    git push origin main
    ```

3. **Automatic tagging**: the `tag-release` workflow detects the version change in `pyproject.toml`, checks that the tag doesn't already exist, and creates and pushes the Git tag automatically. No manual tagging is required.

4. **Publish to PyPI** (maintainers only):

    ```bash
    python -m build
    python -m twine upload dist/*
    ```
