# Development Guide

This guide provides information for developers who want to contribute to or extend Recursivist.

## Setting Up Development Environment

### Prerequisites

- Python 3.7 or higher
- Git
- pip (Python package manager)

### Clone the Repository

```bash
git clone https://github.com/username/recursivist.git
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

Recursivist is organized into several key modules:

```
recursivist/
├── __init__.py          # Package initialization, version info
├── cli.py               # Command-line interface (Typer-based)
├── core.py              # Core functionality (directory traversal, tree building)
├── exports.py           # Export functionality (TXT, JSON, HTML, MD, JSX)
├── compare.py           # Comparison functionality (side-by-side diff)
└── jsx_export.py        # React component generation
```

### Module Responsibilities

- **cli.py**: Defines the command-line interface using Typer, handles command-line arguments and option parsing, and invokes core functionality
- **core.py**: Implements the core directory traversal, pattern matching, and tree building functionality
- **exports.py**: Contains the `DirectoryExporter` class for exporting directory structures to various formats
- **compare.py**: Implements functionality for comparing two directory structures side by side
- **jsx_export.py**: Provides specialized functionality for generating React components

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

5. Push your changes:

   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a pull request.

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

3. Update the format map in the `export_structure` function in `core.py`:

```python
format_map = {
    "txt": exporter.to_txt,
    "json": exporter.to_json,
    "html": exporter.to_html,
    "md": exporter.to_markdown,
    "jsx": exporter.to_jsx,
    "your_format": exporter.to_your_format,  # Add your format here
}
```

4. Add tests for your new export format.

### Adding New File Statistics

To add a new statistic (beyond LOC, size, and mtime):

1. Update the `get_directory_structure` function in `core.py` to collect your new statistic.
2. Add appropriate parameters to the function signature for enabling/sorting by the new statistic.
3. Update the `build_tree` function to display the new statistic.
4. Update export formats to include the new statistic.
5. Add CLI options in `cli.py` to enable the new statistic.

## Testing

For detailed information about testing, see the [Testing Guide](testing.md).

### Basic Testing

```bash
# Run all tests
pytest

# Run tests with code coverage
pytest --cov=recursivist --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run tests matching a pattern
pytest -k "pattern"
```

## Debugging

### Verbose Output

Use the `--verbose` flag during development to enable detailed logging:

```bash
recursivist visualize --verbose
```

This provides more information about what's happening during execution, which can be helpful for debugging.

### Using a Debugger

For complex issues, you can use a debugger:

```python
import pdb
pdb.set_trace()  # Add this line at the point where you want to start debugging
```

With modern IDEs like VSCode or PyCharm, you can also set breakpoints and use their built-in debuggers.

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

When working with large directories:

1. Use generators and iterators where possible to minimize memory usage.
2. Implement early filtering to reduce the number of files and directories processed.
3. Use progress indicators (like the `Progress` class from Rich) for long-running operations.
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

## Extending Pattern Matching

Recursivist currently supports glob patterns (default) and regular expressions. To add a new pattern type:

1. Update the `should_exclude` function in `core.py` to handle the new pattern type.
2. Add a new flag to the command-line arguments in `cli.py`.
3. Add appropriate documentation for the new pattern type.
4. Add tests specifically for the new pattern functionality.

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

## Common Development Tasks

### Adding a New Command-Line Option

1. Add the option to the appropriate command functions in `cli.py`:

```python
@app.command()
def visualize(
    # Existing options...
    new_option: bool = typer.Option(
        False, "--new-option", "-n", help="Description of the new option"
    ),
):
    # Pass the new option to the core function
    display_tree(
        # Existing parameters...
        new_option=new_option
    )
```

2. Update the core function to handle the new option:

```python
def display_tree(
    # Existing parameters...
    new_option: bool = False,
):
    # Use the new option in your function
    if new_option:
        # Do something
        pass
```

### Improving Colorization

The file extension colorization is handled by the `generate_color_for_extension` function in `core.py`:

```python
def generate_color_for_extension(extension: str) -> str:
    """Generate a consistent color for a file extension."""
    # Current implementation uses hash-based approach
    # You can modify this to use predefined colors for common extensions
```

If you want to add predefined colors for common file types:

1. Create a mapping of extensions to colors:

```python
EXTENSION_COLORS = {
    ".py": "#3776AB",  # Python blue
    ".js": "#F7DF1E",  # JavaScript yellow
    ".html": "#E34C26",  # HTML orange
    ".css": "#264DE4",  # CSS blue
    # Add more extensions and colors
}
```

2. Update the `generate_color_for_extension` function to use this mapping:

```python
def generate_color_for_extension(extension: str) -> str:
    """Generate a consistent color for a file extension."""
    extension = extension.lower()
    if extension in EXTENSION_COLORS:
        return EXTENSION_COLORS[extension]
    # Fall back to the hash-based approach for unknown extensions
    # ...
```

This will give common file types consistent, recognizable colors while maintaining the existing behavior for other file types.
