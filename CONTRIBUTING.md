# Contributing to Recursivist

Thank you for your interest in contributing to Recursivist! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Setting Up Your Development Environment](#setting-up-your-development-environment)
  - [Understanding the Project Structure](#understanding-the-project-structure)
- [Development Workflow](#development-workflow)
  - [Creating a Branch](#creating-a-branch)
  - [Making Changes](#making-changes)
  - [Testing Your Changes](#testing-your-changes)
  - [Submitting a Pull Request](#submitting-a-pull-request)
- [Coding Standards](#coding-standards)
  - [Code Style](#code-style)
  - [Documentation](#documentation)
  - [Type Annotations](#type-annotations)
- [Testing](#testing)
  - [Running Tests](#running-tests)
  - [Writing Tests](#writing-tests)
- [Bug Reports and Feature Requests](#bug-reports-and-feature-requests)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
- [Release Process](#release-process)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful, inclusive, and considerate when interacting with other contributors.

## Getting Started

### Setting Up Your Development Environment

1. **Fork the repository**:

   - Visit the [Recursivist repository](https://github.com/ArmaanjeetSandhu/recursivist) and click the "Fork" button to create your own copy.

2. **Clone your fork**:

   ```bash
   git clone https://github.com/YOUR-USERNAME/recursivist.git
   cd recursivist
   ```

3. **Set up the upstream remote**:

   ```bash
   git remote add upstream https://github.com/ArmaanjeetSandhu/recursivist.git
   ```

4. **Create a virtual environment**:

   ```bash
   python -m venv venv

   # Activate the virtual environment
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

5. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

### Understanding the Project Structure

```
recursivist/
├── recursivist/             # Main package directory
│   ├── __init__.py          # Package metadata
│   ├── __main__.py          # Entry point for python -m recursivist
│   ├── cli.py               # Command-line interface
│   ├── core.py              # Core functionality
│   └── exports.py           # Export functionality
├── tests/                   # Test directory
├── LICENSE                  # License file
├── README.md                # Project overview
├── CONTRIBUTING.md          # This file
├── pyproject.toml           # Project metadata and dependencies
└── requirements.txt         # Dependencies
```

## Development Workflow

### Creating a Branch

1. **Make sure your fork is up to date**:

   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

2. **Create a new branch for your feature or bugfix**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

### Making Changes

1. **Make your changes** to the codebase according to our [coding standards](#coding-standards).

2. **Commit your changes** with clear and descriptive commit messages:

   ```bash
   git add .
   git commit -m "Add feature: description of what you added"
   ```

3. **Keep your branch updated** with the upstream repository:
   ```bash
   git pull upstream main
   ```

### Testing Your Changes

1. **Run the tests** to make sure your changes don't break existing functionality:

   ```bash
   pytest
   ```

2. **Test the CLI** to verify it works as expected:
   ```bash
   python -m recursivist --help
   ```

### Submitting a Pull Request

1. **Push your branch** to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** from your fork to the main repository:

   - Go to the [Recursivist repository](https://github.com/ArmaanjeetSandhu/recursivist)
   - Click "Pull Requests" > "New Pull Request"
   - Select "compare across forks" and choose your fork and branch
   - Click "Create Pull Request"

3. **Describe your changes** in the PR:

   - What problem does it solve?
   - How can it be tested?
   - Any dependencies or breaking changes?

4. **Address review feedback** if requested by maintainers.

## Coding Standards

### Code Style

We follow PEP 8 and use the following tools to maintain code quality:

- **Black** for code formatting:

  ```bash
  pip install black
  black recursivist/
  ```

- **Flake8** for linting:

  ```bash
  pip install flake8
  flake8 recursivist/
  ```

- **isort** for import sorting:
  ```bash
  pip install isort
  isort recursivist/
  ```

### Documentation

- Write docstrings for all public modules, functions, classes, and methods.
- Follow the Google docstring style as shown in existing code.
- Update the README.md when introducing new features.

Example docstring:

```python
def function(arg1: str, arg2: int) -> bool:
    """A short description of the function.

    A more detailed description explaining the behavior,
    edge cases, and implementation details if relevant.

    Args:
        arg1: Description of the first argument
        arg2: Description of the second argument

    Returns:
        Description of the return value

    Raises:
        ValueError: When the input is invalid
    """
```

### Type Annotations

We use Python type hints for better code quality and IDE support:

```python
from typing import Dict, List, Optional, Set

def process_data(data: Dict[str, List[str]],
                 options: Optional[Set[str]] = None) -> bool:
    # Function implementation
    return True
```

## Testing

### Running Tests

We use pytest for testing:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=recursivist

# Run tests from a specific file
pytest tests/test_core.py
```

### Writing Tests

- Write tests for all new features and bug fixes.
- Place tests in the `tests/` directory with a name that matches the module being tested.
- Follow the test style used in existing tests.

Example test:

```python
# tests/test_core.py
from recursivist.core import generate_color_for_extension

def test_generate_color_for_extension():
    # Given
    extension = ".py"

    # When
    color = generate_color_for_extension(extension)

    # Then
    assert isinstance(color, str)
    assert color.startswith("#")
    assert len(color) == 7
```

## Bug Reports and Feature Requests

### Reporting Bugs

Please report bugs by opening an issue on GitHub with the following information:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Any relevant logs or screenshots

### Suggesting Features

We welcome feature requests! Please open an issue with:

- A clear and descriptive title
- A detailed description of the proposed feature
- Any relevant examples or use cases
- Information about why this feature would be useful

## Release Process

1. **Version bump**:

   - Update version in `__init__.py` and `pyproject.toml`
   - Update the changelog

2. **Create a release commit**:

   ```bash
   git add .
   git commit -m "Release v0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

3. **Build and publish**:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Community

- **GitHub Discussions**: Use this for questions and general discussion.
- **Issues**: Bug reports and feature requests.
- **Pull Requests**: Submit changes to the codebase.

---

Thank you for contributing to Recursivist! Your efforts help make this project better for everyone.
