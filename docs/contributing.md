# Contributing to Recursivist

Thank you for your interest in contributing to Recursivist! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Setting Up Your Development Environment](#setting-up-your-development-environment)
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
   git clone https://github.com/YOUR_USERNAME/recursivist.git
   cd recursivist
   ```

3. **Install uv** (used for all environment and dependency management):

   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

4. **Create a virtual environment and install development dependencies**:

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```

5. **Install pre-commit hooks**:

   ```bash
   uv pip install pre-commit
   pre-commit install
   ```

   The pre-commit hooks will automatically run Ruff (lint + format) and mypy/pyright type checks on every commit.

## Development Workflow

### Creating a Branch

1. **Create a new branch for your feature or bugfix**:

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

   Pre-commit hooks will run automatically on commit. If they flag issues, fix them and commit again.

3. **Keep your branch updated** with the upstream repository by syncing your fork on GitHub and pulling locally:

   ```bash
   git pull origin main
   ```

### Testing Your Changes

We use [Nox](https://nox.thea.codes/) as the task runner. All sessions run inside isolated uv-managed virtual environments.

1. **Run the full test suite** across all supported Python versions:

   ```bash
   nox -s tests
   ```

2. **Run linting and type checks**:

   ```bash
   nox -s lint typecheck
   ```

3. **Build and preview the documentation**:

   ```bash
   nox -s docs
   ```

4. **Test the CLI** to verify it works as expected:

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

We use [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting. You can run it directly or via Nox:

```bash
# Lint and auto-fix
ruff check --fix .

# Format
ruff format .

# Or run both via Nox
nox -s lint
```

Ruff is also run automatically by the pre-commit hooks on every commit.

### Documentation

- Write docstrings for all public modules, functions, classes, and methods.
- Follow the Google docstring style as shown in existing code.

Example docstring:

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

### Type Annotations

All code must pass both **mypy** (strict mode) and **pyright** type checks. Use standard type hints:

```python
def process_data(
   data: dict[str, list[str]],
   options: set[str] | None = None,
) -> bool:
   return True
```

Run type checks via Nox:

```bash
nox -s typecheck
```

This will run both `mypy --strict` and `pyright` against the codebase.

## Testing

### Running Tests

We use [pytest](https://pytest.org/) via Nox. Coverage reporting is enabled by default (configured in `pyproject.toml`).

```bash
# Run tests across all supported Python versions (3.9–3.13)
nox -s tests

# Pass extra arguments to pytest (e.g. run a specific test)
nox -s tests -- -k test_something

# Run pytest directly in your active environment
pytest
```

### Writing Tests

- Write tests for all new features and bug fixes.
- Place tests in the `tests/` directory with a name matching the module being tested (e.g. `tests/test_core.py`).
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

Releases are largely automated via GitHub Actions.

1. **Bump the version** in `pyproject.toml`:

   ```toml
   version = "X.Y.Z"
   ```

2. **Commit and push to `main`**:

   ```bash
   git add pyproject.toml
   git commit -m "Release vX.Y.Z"
   git push origin main
   ```

3. **Automatic tagging**: The `tag-release` workflow detects the version change in `pyproject.toml`, checks that the tag doesn't already exist, and creates and pushes the Git tag automatically. No manual tagging is required.

4. **Publish to PyPI** (maintainers only):

   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Community

- **GitHub Discussions** Use this for questions and general discussion.
- **Issues** Bug reports and feature requests.
- **Pull Requests** Submit changes to the codebase.

---

Thank you for contributing to Recursivist! Your efforts help make this project better for everyone.
