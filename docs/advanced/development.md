# Development Guide

This guide provides information for developers who want to contribute to or extend Recursivist.

## Setting Up Development Environment

### Prerequisites

- Python 3.7 or higher
- Git
- pip (Python package manager)

### Clone the Repository

```bash
git clone https://github.com/ArmaanjeetSandhu/recursivist.git
cd recursivist
```

### Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### Install Development Dependencies

```bash
# Install the package in development mode with development dependencies
pip install -e ".[dev]"
```

This installs Recursivist in "editable" mode, so your changes to the source code will be reflected immediately without reinstalling.

## Project Structure

Recursivist is organized into several modules:

- `cli.py`: Command-line interface using Typer
- `core.py`: Core functionality for directory traversal and structure building
- `exports.py`: Functionality for exporting directory structures
- `compare.py`: Functionality for comparing directory structures
- `jsx_export.py`: Specialized functionality for React component export

## Development Workflow

### Making Changes

1. Create a new branch for your feature or bug fix:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes to the codebase.

3. Run the tests to ensure your changes don't break existing functionality:

   ```bash
   pytest
   ```

4. Add and commit your changes:

   ```bash
   git add .
   git commit -m "Add your meaningful commit message here"
   ```

5. Push your changes to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a pull request on GitHub.

### Code Style

Recursivist follows PEP 8 style guidelines. We recommend using the following tools for code formatting and linting:

- **Black** for code formatting:

  ```bash
  black recursivist tests
  ```

- **Flake8** for code linting:

  ```bash
  flake8 recursivist tests
  ```

- **MyPy** for type checking:
  ```bash
  mypy recursivist
  ```

## Adding a New Feature

### Adding a New Command

To add a new command to the CLI:

1. Open `cli.py`
2. Add your new command using the Typer decorator pattern:

```python
@app.command()
def your_command(
    directory: Path = typer.Argument(
        ".", help="Directory path to process"
    ),
    # Add more parameters as needed
):
    """
    Your command description.

    Detailed information about what the command does and how to use it.
    """
    # Implement your command logic here
    pass
```

3. Implement the core functionality in the appropriate module.
4. Add tests for your new command.

### Adding a New Export Format

To add a new export format:

1. Open `exports.py`
2. Add a new method to the `DirectoryExporter` class:

```python
def to_your_format(self, output_path: str) -> None:
    """Export directory structure to your format.

    Args:
        output_path: Path where the export file will be saved
    """
    # Implement export to your format
    try:
        # Your export logic here
        with open(output_path, "w", encoding="utf-8") as f:
            # Write your formatted output
            pass
    except Exception as e:
        logger.error(f"Error exporting to YOUR_FORMAT: {e}")
        raise
```

3. Update the `export_structure` function in `core.py` to support your new format.
4. Add tests for your new export format.

## Testing

### Running Tests

To run all tests:

```bash
pytest
```

To run specific test files:

```bash
pytest tests/test_core.py
```

To generate a coverage report:

```bash
pytest --cov=recursivist --cov-report=html
```

This creates an HTML coverage report in the `htmlcov` directory.

### Writing Tests

Test files are located in the `tests` directory. We use pytest for testing.

When writing tests, follow these guidelines:

1. Structure your tests with clear, descriptive names.
2. Test both normal and edge case behaviors.
3. Use fixtures and parametrization where appropriate.
4. Mock external dependencies when necessary.

Example test:

```python
def test_get_directory_structure_with_exclude_dirs(tmp_path):
    # Setup
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    (root_dir / "include_dir").mkdir()
    (root_dir / "exclude_dir").mkdir()
    (root_dir / "include_dir" / "file.txt").write_text("content")
    (root_dir / "exclude_dir" / "file.txt").write_text("content")

    # Execute
    structure, _ = get_directory_structure(
        str(root_dir), exclude_dirs=["exclude_dir"]
    )

    # Assert
    assert "include_dir" in structure
    assert "exclude_dir" not in structure
    assert "_files" in structure["include_dir"]
    assert "file.txt" in structure["include_dir"]["_files"]
```

## Building and Distribution

### Building the Package

To build the package:

```bash
# Install build tools if not already installed
pip install build

# Build the package
python -m build
```

This creates distribution packages in the `dist` directory.

### Running the CLI During Development

While developing, you can run the CLI directly:

```bash
# Using Python
python -m recursivist.cli visualize

# Using the installed development version
recursivist visualize
```

## Debugging

### Verbose Output

Use the `--verbose` flag to enable detailed logging:

```bash
recursivist visualize --verbose
```

This provides more information about what's happening during execution, which can be helpful for debugging.

### Debugging Specific Modules

You can set up logging for specific modules to get more detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('recursivist.core')
```

### Using a Debugger

For more complex issues, you can use a debugger like `pdb` or an IDE debugger:

```python
import pdb
pdb.set_trace()  # Add this line at the point where you want to start debugging
```

## Documentation

### Docstrings

Use Google-style docstrings for all functions, classes, and methods:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Short description of the function.

    More detailed description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why this exception is raised
    """
    # Function implementation
```

### Command-Line Help

Update the command-line help text when you add or modify commands or options:

```python
@app.command()
def your_command(
    param: str = typer.Option(
        None, "--param", "-p", help="Clear description of the parameter"
    )
):
    """
    Clear, concise description of what the command does.

    More detailed explanation with examples:

    Examples:
        recursivist your_command --param value
    """
    # Implementation
```

## Performance Considerations

### Large Directory Structures

When working with large directory structures:

1. Use generators and iterators where possible to minimize memory usage.
2. Implement early filtering to reduce the number of files and directories processed.
3. Consider adding progress indicators for long-running operations.
4. Test with large directories to ensure acceptable performance.

### Profiling

Use the `cProfile` module to profile performance:

```python
import cProfile
cProfile.run('your_function_call()', 'profile_results')

# To analyze the results
import pstats
p = pstats.Stats('profile_results')
p.sort_stats('cumulative').print_stats(20)
```

## Extending Recursivist

### Adding Support for New Pattern Types

To add a new pattern matching type:

1. Update the `should_exclude` function in `core.py`.
2. Add appropriate command-line options in `cli.py`.
3. Add documentation for the new pattern type.
4. Add tests for the new functionality.

### Adding New Visualization Features

To enhance the visualization:

1. Modify the `build_tree` and `display_tree` functions in `core.py`.
2. Ensure the visualization works well in different terminal environments.
3. Update documentation and tests.

## Release Process

### Version Numbering

Recursivist follows Semantic Versioning (SemVer):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible feature additions
- **PATCH** version for backwards-compatible bug fixes

### Creating a Release

1. Update the version in `__init__.py`.
2. Update the CHANGELOG.md file.
3. Commit the changes:
   ```bash
   git add .
   git commit -m "Prepare for release x.y.z"
   ```
4. Create a tag for the release:
   ```bash
   git tag -a vx.y.z -m "Release x.y.z"
   ```
5. Push the changes and tag:
   ```bash
   git push origin main
   git push origin vx.y.z
   ```
6. Build the package:
   ```bash
   python -m build
   ```
7. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

## Getting Help

If you need help with development:

1. Check the existing documentation and code comments
2. Look at the test suite for examples of how components work
3. Create an issue on GitHub for questions or problems
4. Reach out to the maintainers directly
