# Testing Guide

This guide covers the testing framework and practices for Recursivist development. It's intended for contributors who want to add features or fix bugs in the codebase.

## Testing Framework

Recursivist uses pytest for testing. The test suite covers:

- Core functionality (directory traversal, pattern matching, tree building)
- CLI interface (commands, options, argument handling)
- Export formats (TXT, JSON, HTML, MD, JSX)
- Comparison functionality (side-by-side directory comparison)
- Pattern matching (glob patterns, regex patterns)
- File statistics (lines of code, file sizes, modification times)

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Stop on first failure and show traceback
pytest -xvs

# Run a specific test file
pytest tests/test_core.py

# Run tests matching a specific name
pytest -k "pattern"
```

### Coverage Testing

To see how much of the codebase is covered by tests:

```bash
# Basic coverage report
pytest --cov=recursivist

# Detailed HTML coverage report
pytest --cov=recursivist --cov-report=html
```

This creates an HTML report in the `htmlcov` directory that shows which lines of code are covered by tests.

## Test Organization

Tests are organized by module and functionality:

```
tests/
├── test_cli.py          # Command-line interface tests
├── test_core.py         # Core functionality tests
├── test_exports.py      # Export format tests
├── test_compare.py      # Comparison functionality tests
├── test_pattern.py      # Pattern matching tests
├── test_integration.py  # End-to-end integration tests
└── conftest.py          # Test fixtures and configuration
```

Each test file focuses on a specific aspect of the codebase to maintain clear separation of concerns.

## Writing Tests

### Test Structure

Follow this pattern for writing tests:

```python
def test_function_name(fixture1, fixture2):
    """Test description - what is being tested."""
    # 1. Setup - prepare the test conditions
    input_data = ...
    expected_output = ...

    # 2. Exercise - call the function being tested
    actual_output = function_under_test(input_data)

    # 3. Verify - check if the function behaved as expected
    assert actual_output == expected_output

    # 4. Cleanup - if needed (usually handled by pytest fixtures)
```

### Testing Directory Operations

For testing directory operations, use the `tmp_path` fixture:

```python
def test_get_directory_structure(tmp_path):
    # Create a test directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").write_text("content")
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file2.py").write_text("print('hello')")

    # Call the function
    structure, extensions = get_directory_structure(str(tmp_path))

    # Verify the result
    assert "dir1" in structure
    assert "dir2" in structure
    assert "_files" in structure["dir1"]
    assert "file1.txt" in structure["dir1"]["_files"]
    assert ".py" in extensions
```

### Testing CLI Commands

For testing CLI commands, use `typer.testing.CliRunner`:

```python
from typer.testing import CliRunner
from recursivist.cli import app

def test_visualize_command(tmp_path):
    # Setup
    runner = CliRunner()
    (tmp_path / "test_file.txt").write_text("content")

    # Run the command
    result = runner.invoke(app, ["visualize", str(tmp_path)])

    # Verify the result
    assert result.exit_code == 0
    assert "test_file.txt" in result.stdout
```

### Testing Export Formats

For testing export formats:

```python
def test_export_to_markdown(tmp_path):
    # Setup
    (tmp_path / "test_file.txt").write_text("content")
    output_path = tmp_path / "output.md"

    # Run export
    structure, _ = get_directory_structure(str(tmp_path))
    export_structure(structure, str(tmp_path), "md", str(output_path))

    # Verify output file
    assert output_path.exists()
    content = output_path.read_text()
    assert "# 📂" in content
    assert "test_file.txt" in content
```

### Testing with Parametrization

Use parametrized tests for testing multiple scenarios with the same logic:

```python
import pytest

@pytest.mark.parametrize("exclude_dirs, expected_files", [
    (["dir1"], ["dir2/file2.txt"]),
    (["dir2"], ["dir1/file1.txt"]),
    ([], ["dir1/file1.txt", "dir2/file2.txt"])
])
def test_exclude_directories(tmp_path, exclude_dirs, expected_files):
    # Setup
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").write_text("content")
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file2.txt").write_text("content")

    # Get the structure with exclusions
    structure, _ = get_directory_structure(str(tmp_path), exclude_dirs=exclude_dirs)

    # Extract all files from the structure
    all_files = []

    def collect_files(struct, path=""):
        if "_files" in struct:
            for file_item in struct["_files"]:
                if isinstance(file_item, tuple):
                    file_name = file_item[0]
                else:
                    file_name = file_item
                all_files.append(f"{path}/{file_name}" if path else file_name)

        for name, content in struct.items():
            if isinstance(content, dict) and name not in ["_files", "_max_depth_reached", "_loc", "_size", "_mtime"]:
                new_path = f"{path}/{name}" if path else name
                collect_files(content, new_path)

    collect_files(structure)

    # Verify all expected files are found and no unexpected files are present
    assert sorted(all_files) == sorted(expected_files)
```

## Test Fixtures

Use pytest fixtures for shared test setup:

```python
import pytest

@pytest.fixture
def simple_dir_structure(tmp_path):
    """Create a simple directory structure for testing."""
    # Create directories
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "subdir").mkdir()

    # Create files
    (tmp_path / "root_file.txt").write_text("root content")
    (tmp_path / "dir1" / "file1.py").write_text("print('hello')")
    (tmp_path / "dir2" / "file2.js").write_text("console.log('hello')")
    (tmp_path / "dir2" / "subdir" / "file3.css").write_text("body { color: red; }")

    return tmp_path

def test_directory_traversal(simple_dir_structure):
    # Now you can use the fixture
    structure, extensions = get_directory_structure(str(simple_dir_structure))

    # Verify structure
    assert "dir1" in structure
    assert "dir2" in structure
    assert "subdir" in structure["dir2"]

    # Verify extensions
    assert set(extensions) == {".txt", ".py", ".js", ".css"}
```

## Mocking

For testing functions that interact with external systems or have side effects, use mocking:

```python
from unittest.mock import patch, MagicMock

def test_count_lines_of_code():
    # Prepare test content
    file_content = "line 1\nline 2\nline 3\n"

    # Mock the file open operation
    mock_open = MagicMock()
    mock_open.return_value.__enter__.return_value.read.return_value = file_content.encode('utf-8')
    mock_file = MagicMock()
    mock_file.__iter__.return_value = file_content.splitlines()

    # Apply mocks
    with patch('builtins.open', mock_open):
        with patch('recursivist.core.open', mock_open):
            # Run function with mocked file operations
            result = count_lines_of_code("fake_file.py")

            # Verify result
            assert result == 3
```

## Testing Pattern Matching

Test different pattern types (glob, regex) thoroughly:

```python
@pytest.mark.parametrize("pattern, is_regex, paths, expected", [
    # Glob patterns
    ("*.py", False, ["file.py", "file.js", "test.py"], ["file.py", "test.py"]),
    ("test_*.py", False, ["test_file.py", "file_test.py", "test.py"], ["test_file.py"]),

    # Regex patterns
    (r".*\.py$", True, ["file.py", "file.js", "test.py"], ["file.py", "test.py"]),
    (r"^test_.*\.py$", True, ["test_file.py", "file_test.py", "test.py"], ["test_file.py"]),
])
def test_pattern_matching(tmp_path, pattern, is_regex, paths, expected):
    # Create test files
    for path in paths:
        (tmp_path / path).write_text("content")

    # Compile patterns
    patterns = compile_regex_patterns([pattern], is_regex)

    # Get structure with patterns
    structure, _ = get_directory_structure(
        str(tmp_path),
        exclude_patterns=patterns if is_regex else None,
        include_patterns=None
    )

    # Check that only expected files are included
    found_files = structure.get("_files", [])
    found_names = [f[0] if isinstance(f, tuple) else f for f in found_files]

    # If we're using exclude patterns, we expect the opposite
    if pattern in patterns:
        # For exclude patterns, check that no excluded files are present
        for path in paths:
            filename = os.path.basename(path)
            if filename in expected:
                assert filename not in found_names
            else:
                assert filename in found_names
    else:
        # For include patterns, check that only included files are present
        assert sorted(found_names) == sorted([os.path.basename(p) for p in expected])
```

## Testing Statistics

Test the file statistics collection functionality:

```python
def test_file_statistics(tmp_path):
    # Create test files with known content
    py_file = tmp_path / "test.py"
    py_file.write_text("line 1\nline 2\nline 3\n")

    # Get structure with statistics
    structure, _ = get_directory_structure(
        str(tmp_path),
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True
    )

    # Verify LOC statistic
    assert structure["_loc"] == 3

    # Verify size statistic
    py_file_size = os.path.getsize(str(py_file))
    assert structure["_size"] == py_file_size

    # Verify mtime statistic
    py_file_mtime = os.path.getmtime(str(py_file))
    assert structure["_mtime"] == py_file_mtime

    # Verify file structure
    file_item = structure["_files"][0]
    assert isinstance(file_item, tuple)
    assert file_item[0] == "test.py"  # Filename
    assert file_item[2] == 3          # LOC
    assert file_item[3] == py_file_size  # Size
    assert file_item[4] == py_file_mtime  # Mtime
```

## Testing CLI Options

Test various CLI option combinations:

```python
@pytest.mark.parametrize("options, expected_in_output, expected_not_in_output", [
    # Test depth limiting
    (["--depth", "1"], ["dir1"], ["file3.txt"]),

    # Test exclude directories
    (["--exclude", "dir1"], ["dir2"], ["dir1", "file1.txt"]),

    # Test exclude extensions
    (["--exclude-ext", ".txt"], ["file2.py"], ["file1.txt", "file3.txt"]),

    # Test LOC sorting
    (["--sort-by-loc"], ["lines"], []),

    # Test size sorting
    (["--sort-by-size"], ["KB", "B"], []),

    # Test mtime sorting
    (["--sort-by-mtime"], ["Today", "Yesterday"], []),

    # Test multiple options
    (
        ["--exclude", "dir2", "--sort-by-loc", "--depth", "1"],
        ["dir1", "lines"],
        ["dir2", "file3.txt"]
    ),
])
def test_cli_options(tmp_path, options, expected_in_output, expected_not_in_output):
    # Create test directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "subdir").mkdir()
    (tmp_path / "dir1" / "file1.txt").write_text("content\ncontent")
    (tmp_path / "dir2" / "file2.py").write_text("print('hello')\nprint('world')\nprint('!')")
    (tmp_path / "dir2" / "subdir" / "file3.txt").write_text("content")

    # Run command with options
    runner = CliRunner()
    result = runner.invoke(app, ["visualize", str(tmp_path)] + options)

    # Verify exit code
    assert result.exit_code == 0

    # Verify expected content in output
    for text in expected_in_output:
        assert text in result.stdout

    # Verify expected content not in output
    for text in expected_not_in_output:
        assert text not in result.stdout
```

## Debugging Tests

When a test fails:

1. Run with `-xvs` to stop at the first failure and show detailed output:

   ```bash
   pytest -xvs tests/test_file.py::test_function
   ```

2. Add print statements or use `pytest.set_trace()` for debugging:

   ```python
   def test_function():
       result = function_under_test()
       print(f"Result: {result}")  # Will show in pytest output with -v
       import pytest; pytest.set_trace()  # Will stop and start a debugger
       assert result == expected
   ```

3. Use the `--pdb` flag to drop into the debugger on failures:

   ```bash
   pytest --pdb
   ```

## Testing Complex Directory Structures

For testing complex directory hierarchies:

```python
def create_complex_structure(tmp_path):
    """Create a more complex directory structure for testing."""
    # Project root files
    (tmp_path / "README.md").write_text("# Project\n\nDescription")
    (tmp_path / ".gitignore").write_text("node_modules/\n*.pyc\n")

    # Source code
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def main():\n    print('Hello')\n\nif __name__ == '__main__':\n    main()")
    (src / "utils.py").write_text("def helper():\n    return 'helper'")

    # Tests
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_main.py").write_text("def test_main():\n    assert True")
    (tests / "test_utils.py").write_text("def test_helper():\n    assert True")

    # Build artifacts
    build = tmp_path / "build"
    build.mkdir()
    (build / "output.min.js").write_text("console.log('minified')")

    # Nested directories
    (src / "components").mkdir()
    (src / "components" / "button.py").write_text("class Button:\n    pass")
    (src / "components" / "form.py").write_text("class Form:\n    pass")

    return tmp_path

def test_large_directory_structure():
    """Test handling of a larger directory structure."""
    tmp_path = create_complex_structure(tmp_path_factory.getbasetemp())

    # Test various scenarios with the complex structure
    # ...
```

## Testing Edge Cases

Always test edge cases and potential failure conditions:

```python
def test_empty_directory(tmp_path):
    """Test behavior with an empty directory."""
    # Empty directory
    structure, extensions = get_directory_structure(str(tmp_path))
    assert "_files" not in structure
    assert len(extensions) == 0

def test_nonexistent_directory():
    """Test behavior with a nonexistent directory."""
    with pytest.raises(Exception):
        get_directory_structure("/nonexistent/directory")

def test_permission_denied(tmp_path, monkeypatch):
    """Test behavior when permission is denied."""
    # Mock os.listdir to raise PermissionError
    def mock_listdir(path):
        raise PermissionError("Permission denied")

    monkeypatch.setattr(os, "listdir", mock_listdir)

    # Should handle permission error gracefully
    structure, extensions = get_directory_structure(str(tmp_path))
    assert structure == {}
    assert not extensions

def test_with_binary_files(tmp_path):
    """Test behavior with binary files."""
    # Create a binary file
    binary_file = tmp_path / "binary.bin"
    with open(binary_file, "wb") as f:
        f.write(b"\x00\x01\x02\x03")

    # Should handle binary files properly for LOC counting
    structure, _ = get_directory_structure(str(tmp_path), sort_by_loc=True)

    # Binary files should have 0 lines
    assert structure["_loc"] == 0
```

## Continuous Integration Testing

Run tests in CI environments to catch platform-specific issues:

```yaml
# Example GitHub Actions workflow
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.7", "3.8", "3.9", "3.10", "3.11"]

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest --cov=recursivist
```

## Test-Driven Development

For adding new features, consider using Test-Driven Development (TDD):

1. Write a failing test that defines the expected behavior
2. Implement the minimal code to make the test pass
3. Refactor the code while keeping the tests passing

This approach ensures your new feature has test coverage from the start and helps clarify the requirements before implementation.

## Test Best Practices

1. **Keep tests independent**: Each test should run in isolation.
2. **Test one thing per test**: Focus each test on a specific behavior.
3. **Use descriptive test names**: Make it clear what is being tested.
4. **Test failure cases**: Include tests for expected failures and edge cases.
5. **Keep tests fast**: Optimize tests to run quickly to encourage frequent testing.
6. **Maintain test coverage**: Add tests for new features and bug fixes.
7. **Test real-world scenarios**: Include tests that reflect how users will actually use the software.
8. **Refactor tests when needed**: Keep test code clean and maintainable.

Following these testing practices will help ensure Recursivist remains stable and reliable as it evolves.
