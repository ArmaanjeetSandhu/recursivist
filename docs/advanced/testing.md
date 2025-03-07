# Testing

This guide covers the testing framework and practices used in Recursivist. It's intended for developers who want to contribute to the project or extend its functionality.

## Test Framework

Recursivist uses pytest for testing. The test suite covers core functionality, CLI interface, export features, comparison functionality, regex pattern matching, and depth limiting.

## Running Tests

### Basic Test Commands

To run all tests:

```bash
pytest
```

To run specific test files:

```bash
# Run only core tests
pytest tests/test_core.py

# Run only export tests
pytest tests/test_exports.py

# Run only CLI tests
pytest tests/test_cli.py
```

### Additional Testing Options

To run tests with verbose output:

```bash
pytest -v
```

To stop on the first failing test:

```bash
pytest -xvs
```

To run tests that match a specific name pattern:

```bash
pytest -k "pattern"
```

For example, to run all tests related to exclusion:

```bash
pytest -k "exclude"
```

## Test Coverage

To generate a test coverage report:

```bash
pytest --cov=recursivist
```

For a more detailed HTML coverage report:

```bash
pytest --cov=recursivist --cov-report=html
```

This will create an HTML coverage report in the `htmlcov` directory, which you can open in your browser.

## Test Structure

The tests are organized into several categories:

### Unit Tests

Test individual functions and classes in isolation:

- `test_core.py`: Tests for directory structure generation and manipulation
- `test_exports.py`: Tests for export functionality
- `test_compare.py`: Tests for comparison functionality

### Integration Tests

Test how different components work together:

- `test_cli.py`: Tests for the command-line interface
- `test_integration.py`: End-to-end tests for core functionality

### Edge Case Tests

Test boundary conditions and error handling:

- `test_regex.py`: Tests for regex pattern matching
- `test_depth.py`: Tests for depth limiting functionality

## Writing Tests

When writing tests for Recursivist, follow these guidelines:

### Directory Structure Tests

For testing directory structure generation and traversal, use the `tmp_path` fixture:

```python
def test_get_directory_structure(tmp_path):
    # Create a temporary directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").write_text("content")
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file2.txt").write_text("content")

    # Get the directory structure
    structure, extensions = get_directory_structure(str(tmp_path))

    # Assert expected structure
    assert "dir1" in structure
    assert "dir2" in structure
    assert "_files" in structure["dir1"]
    assert "file1.txt" in structure["dir1"]["_files"]
```

### CLI Tests

For testing the command-line interface, use the `typer.testing.CliRunner`:

```python
from typer.testing import CliRunner
from recursivist.cli import app

def test_visualize_command(tmp_path):
    # Setup
    runner = CliRunner()
    (tmp_path / "test_file.txt").write_text("content")

    # Run the command
    result = runner.invoke(app, ["visualize", str(tmp_path)])

    # Assert
    assert result.exit_code == 0
    assert "test_file.txt" in result.stdout
```

### Export Tests

For testing export functionality, check both the output file existence and content:

```python
def test_export_to_markdown(tmp_path):
    # Setup
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir" / "file.txt").write_text("content")
    output_path = tmp_path / "output.md"

    # Execute
    export_structure(
        {"dir": {"_files": ["file.txt"]}},
        str(tmp_path),
        "md",
        str(output_path)
    )

    # Assert
    assert output_path.exists()
    content = output_path.read_text()
    assert "# 📂" in content
    assert "dir" in content
    assert "file.txt" in content
```

### Comparison Tests

For testing comparison functionality, create two temporary directory structures:

```python
def test_compare_directory_structures(tmp_path):
    # Setup
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()
    (dir1 / "common.txt").write_text("content")
    (dir1 / "only_in_dir1.txt").write_text("content")
    (dir2 / "common.txt").write_text("content")
    (dir2 / "only_in_dir2.txt").write_text("content")

    # Execute
    struct1, struct2, extensions = compare_directory_structures(
        str(dir1), str(dir2)
    )

    # Assert
    assert "_files" in struct1
    assert "_files" in struct2
    assert "common.txt" in struct1["_files"]
    assert "common.txt" in struct2["_files"]
    assert "only_in_dir1.txt" in struct1["_files"]
    assert "only_in_dir1.txt" not in struct2["_files"]
    assert "only_in_dir2.txt" not in struct1["_files"]
    assert "only_in_dir2.txt" in struct2["_files"]
```

## Test Data

For tests that require more complex data structures, use fixtures:

```python
import pytest

@pytest.fixture
def complex_directory_structure():
    return {
        "dir1": {
            "_files": ["file1.txt", "file2.py"],
            "subdir1": {
                "_files": ["file3.js", "file4.css"]
            }
        },
        "dir2": {
            "_files": ["file5.md"]
        },
        "_files": ["root_file.txt"]
    }

def test_with_complex_structure(complex_directory_structure):
    # Use the fixture in your test
    result = some_function(complex_directory_structure)
    assert result == expected_result
```

## Mocking

For tests that need to mock external dependencies or file system interactions, use `unittest.mock`:

```python
from unittest.mock import patch, mock_open

def test_with_mocked_filesystem():
    mock_file_content = "file content"
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch("os.path.exists", return_value=True):
            # Test code that reads from files
            result = function_that_reads_file("dummy/path")
            assert result == expected_result
```

## Parametrized Tests

For testing multiple scenarios with the same test function, use pytest's parametrize:

```python
@pytest.mark.parametrize("exclude_dirs,expected_result", [
    (["dir1"], {"dir2": {"_files": ["file.txt"]}}),
    (["dir2"], {"dir1": {"_files": ["file.txt"]}}),
    ([], {"dir1": {"_files": ["file.txt"]}, "dir2": {"_files": ["file.txt"]}})
])
def test_exclude_dirs(tmp_path, exclude_dirs, expected_result):
    # Setup
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file.txt").write_text("content")
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file.txt").write_text("content")

    # Execute
    structure, _ = get_directory_structure(str(tmp_path), exclude_dirs=exclude_dirs)

    # Assert structure matches expected result
    # (This is a simplified example, you'd need to adapt the assertion for real tests)
    assert set(structure.keys()) == set(expected_result.keys())
```

## Continuous Integration Testing

Recursivist uses GitHub Actions for continuous integration testing. The workflow is defined in `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.6, 3.7, 3.8, 3.9, "3.10"]

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
          pytest
```

This ensures that every push to the main branch and every pull request is tested across multiple Python versions.

## Test Debugging

If a test is failing and you need to debug it:

1. Use the `-xvs` flag to stop on the first failure and show detailed output:

   ```bash
   pytest -xvs
   ```

2. Add print statements or use the built-in debugger:

   ```python
   import pdb

   def test_something():
       # ... test setup ...
       result = function_to_test()
       pdb.set_trace()  # This will start the debugger
       assert result == expected
   ```

3. For more complex debugging, use the `--pdb` flag to drop into the debugger on test failures:
   ```bash
   pytest --pdb
   ```

## Common Testing Patterns

### Testing File Exclusions

```python
def test_exclude_extensions(tmp_path):
    # Setup
    (tmp_path / "file1.txt").write_text("content")
    (tmp_path / "file2.log").write_text("content")

    # Execute
    structure, _ = get_directory_structure(
        str(tmp_path), exclude_extensions={".log"}
    )

    # Assert
    assert "_files" in structure
    assert "file1.txt" in structure["_files"]
    assert "file2.log" not in structure["_files"]
```

### Testing Pattern Matching

```python
def test_exclude_patterns(tmp_path):
    # Setup
    (tmp_path / "file.txt").write_text("content")
    (tmp_path / "test_file.txt").write_text("content")

    # Execute
    structure, _ = get_directory_structure(
        str(tmp_path), exclude_patterns=["test_*"]
    )

    # Assert
    assert "_files" in structure
    assert "file.txt" in structure["_files"]
    assert "test_file.txt" not in structure["_files"]
```

### Testing Depth Limiting

```python
def test_depth_limiting(tmp_path):
    # Setup
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "subdir").mkdir()
    (tmp_path / "dir1" / "subdir" / "file.txt").write_text("content")

    # Execute
    structure, _ = get_directory_structure(str(tmp_path), max_depth=1)

    # Assert
    assert "dir1" in structure
    assert "_max_depth_reached" in structure["dir1"]
    assert "subdir" not in structure["dir1"]
```

## Testing Best Practices

1. **Test isolation**: Each test should be independent and not rely on the state from other tests.

2. **Descriptive names**: Use descriptive test names that explain what is being tested.

3. **Arrange-Act-Assert**: Structure your tests with clear setup, action, and assertion phases.

4. **Test edge cases**: Include tests for boundary conditions, empty inputs, large inputs, etc.

5. **Keep tests simple**: Each test should verify a single aspect of behavior.

6. **Clean up test resources**: Use fixtures and proper teardown to clean up temporary resources.

7. **Maintain test coverage**: Aim for high test coverage, especially for critical code paths.

8. **Document test requirements**: Include comments explaining the purpose and requirements of complex tests.
