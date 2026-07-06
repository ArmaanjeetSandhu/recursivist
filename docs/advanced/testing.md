# Testing Guide

This guide covers Recursivist's test suite and conventions. It's intended for contributors adding features or fixing bugs.

## Framework

Recursivist uses [pytest](https://pytest.org/), with [Hypothesis](https://hypothesis.readthedocs.io/) for property-based tests and [Nox](https://nox.thea.codes/) as the task runner. Tests run across Python 3.10–3.14 in isolated environments. Coverage reporting is enabled by default through `addopts` in `pyproject.toml`.

The suite exercises directory scanning, filtering, sorting, tree rendering, every export format, comparison, file statistics, Git status, colorization, and the CLI.

## Running Tests

```bash
# Full suite across all supported Python versions
nox -s tests

# Pass arguments through to pytest
nox -s tests -- -v
nox -s tests -- tests/test_scanner.py
nox -s tests -- -k "pattern"

# Run pytest directly in the active environment
pytest
pytest -xvs tests/test_filtering.py
```

Coverage prints automatically — no extra flags are needed.

### Markers

Two custom markers are defined:

- `integration`: end-to-end tests that build real directory trees and invoke the CLI.
- `property`: Hypothesis property-based tests.

```bash
pytest -m integration       # only integration tests
pytest -m "not property"    # skip property-based tests
```

## Test Organization

Tests mirror the package's modules:

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── helpers.py           # Test helper utilities
├── strategies.py        # Hypothesis strategies for property tests
├── test_cli.py          # Command-line interface
├── test_flags.py        # Flag resolution (DisplayOptions, command-line order)
├── test_models.py       # FileEntry and positional coercion
├── test_scanner.py      # Directory traversal
├── test_tree.py         # Tree rendering
├── test_filtering.py    # Exclusion, glob, and regex logic
├── test_sorting.py      # File ordering and similarity grouping
├── test_metrics.py      # Lines of code, size, mtime
├── test_colors.py       # Per-extension colors
├── test_git_status.py   # Git status lookup
├── test_exporters.py    # Export formats
├── test_compare.py      # Directory comparison
└── test_integration.py  # End-to-end scenarios
```

## Writing Tests

### Directory Operations

Use the `tmp_path` fixture to build a structure on disk:

```python
from recursivist.scanner import get_directory_structure


def test_get_directory_structure(tmp_path):
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").write_text("content")
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file2.py").write_text("print('hello')")

    structure, extensions = get_directory_structure(str(tmp_path))

    assert "dir1" in structure
    assert "file1.txt" in structure["dir1"]["_files"]
    assert ".py" in extensions
```

### CLI Commands

Use Typer's `CliRunner`:

```python
from typer.testing import CliRunner
from recursivist.cli import app


def test_visualize_command(tmp_path):
    (tmp_path / "test_file.txt").write_text("content")
    result = CliRunner().invoke(app, ["visualize", str(tmp_path)])

    assert result.exit_code == 0
    assert "test_file.txt" in result.stdout
```

### Export Formats

Construct an exporter via the factory and check the output:

```python
from recursivist.scanner import get_directory_structure
from recursivist.exporters import get_exporter


def test_export_to_markdown(tmp_path):
    (tmp_path / "test_file.txt").write_text("content")
    output_path = tmp_path / "output.md"

    structure, _ = get_directory_structure(str(tmp_path))
    get_exporter("md", structure=structure, root_name=tmp_path.name).export(str(output_path))

    content = output_path.read_text()
    assert "# 📁" in content
    assert "test_file.txt" in content
```

### File Statistics

`_files` entries are `FileEntry` tuples with fields `(name, path, loc, size, mtime)`. Read them by attribute (after normalizing with `FileEntry.from_raw`) or by index, since `FileEntry` subclasses `tuple`:

```python
import os

from recursivist.scanner import get_directory_structure
from recursivist._models import FileEntry


def test_file_statistics(tmp_path):
    py_file = tmp_path / "test.py"
    py_file.write_text("line 1\nline 2\nline 3\n")

    structure, _ = get_directory_structure(
        str(tmp_path), sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )

    assert structure["_loc"] == 3
    assert structure["_size"] == os.path.getsize(str(py_file))

    entry = FileEntry.coerce(structure["_files"][0])
    assert entry.name == "test.py"
    assert entry.loc == 3
    assert isinstance(entry, tuple)  # still a tuple
```

### Parametrization

Cover several scenarios with one test body:

```python
import pytest

from recursivist.scanner import get_directory_structure


@pytest.mark.parametrize(
    "exclude_dirs, expected",
    [
        (["dir1"], ["file2.py"]),
        (["dir2"], ["file1.txt"]),
        ([], ["file1.txt", "file2.py"]),
    ],
)
def test_exclude_directories(tmp_path, exclude_dirs, expected):
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").write_text("x")
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file2.py").write_text("x")

    structure, _ = get_directory_structure(str(tmp_path), exclude_dirs=exclude_dirs)

    names = []
    for key, value in structure.items():
        if isinstance(value, dict):
            names += [f if isinstance(f, str) else f[0] for f in value.get("_files", [])]
    assert sorted(names) == sorted(expected)
```

### Property-Based Tests

Property tests use Hypothesis with strategies defined in `tests/strategies.py` and are marked `property`. They assert invariants over many generated inputs (for example, that scanning never raises on arbitrary valid trees, or that a name always survives a round trip through `FileEntry.from_raw`). Mark new ones accordingly:

```python
import pytest
from hypothesis import given


@pytest.mark.property
@given(...)  # a strategy from tests/strategies.py
def test_invariant(value):
    ...
```

## Fixtures and Mocking

Put shared setup in `conftest.py` as fixtures, and reuse utilities from `helpers.py`. Use `monkeypatch` or `unittest.mock` for filesystem edge cases:

```python
import os


def test_permission_denied(tmp_path, monkeypatch):
    def deny(_):
        raise PermissionError("denied")

    monkeypatch.setattr(os, "listdir", deny)
    structure, extensions = get_directory_structure(str(tmp_path))
    assert structure == {}
    assert not extensions
```

## Edge Cases

Always cover empty directories, nonexistent paths, permission errors, and binary files:

```python
def test_binary_files(tmp_path):
    (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02\x03")
    structure, _ = get_directory_structure(str(tmp_path), sort_by_loc=True)
    assert structure["_loc"] == 0  # binary files count as 0 lines
```

## Debugging Failing Tests

```bash
# Stop at the first failure with verbose output
pytest -xvs tests/test_scanner.py::test_function

# Drop into the debugger on failure
pytest --pdb
```

You can also add `breakpoint()` inside a test to start an interactive session at that point.

## Continuous Integration

Tests run automatically on every push and pull request via GitHub Actions, exercising the full suite across Python 3.10–3.14 with Nox. Push your branch and check the results — no local CI configuration is needed.

## Best Practices

Keep tests independent and fast, focus each test on one behavior, use descriptive names, cover failure cases and edge cases alongside the happy path, and add tests for every new feature or bug fix.
