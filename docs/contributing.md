# Contributing to Recursivist

Thank you for your interest in contributing to Recursivist! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## Getting Started

### Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/recursivist.git
   cd recursivist
   ```
3. Create a virtual environment and install development dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

This installs Recursivist in development mode, along with all the development tools.

### Running Tests

Recursivist uses pytest for testing. To run all tests:

```bash
pytest
```

To run specific test files:

```bash
# Run only core tests
pytest test_core.py

# Run only export tests
pytest test_exports.py
```

To generate a test coverage report:

```bash
pytest --cov=recursivist --cov-report=html
```

This creates an HTML coverage report in the `htmlcov` directory.

## Making Changes

### Branching Strategy

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and commit them with descriptive commit messages
3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

### Style Guidelines

Recursivist follows PEP 8 style guidelines for Python code. We use:

- Black for code formatting
- Flake8 for linting
- MyPy for type checking

You can check your code style with:

```bash
# Format code
black recursivist tests

# Check style
flake8 recursivist tests

# Check types
mypy recursivist
```

### Documentation

When adding new features, please update the documentation accordingly:

- Add docstrings to new functions and classes following Google-style format
- Update command-line help text if you modify the CLI
- Update the README if necessary
- Consider adding examples for new features

## Submitting Changes

1. Make sure all tests pass:

   ```bash
   pytest
   ```

2. Push your changes to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a pull request on GitHub from your fork to the main repository

4. In your pull request description, explain:
   - What problems your changes solve
   - How your changes address these problems
   - Any additional context that might be helpful for review

## Pull Request Process

1. Ensure your code includes appropriate tests and documentation
2. Update the README.md if needed, including examples for new features
3. The pull request will be reviewed by maintainers, who may suggest changes
4. Once approved, your pull request will be merged

## Adding a New Feature

If you're adding a new feature to Recursivist:

1. First, open an issue to discuss the feature
2. Once the feature is approved, create a branch and implement it
3. Write tests to cover the new functionality
4. Update documentation to explain the new feature
5. Submit a pull request

## Reporting Bugs

If you find a bug in Recursivist:

1. Check if the bug has already been reported in the GitHub Issues
2. If not, create a new issue with:
   - A clear title that summarizes the issue
   - A detailed description of the bug
   - Steps to reproduce it
   - Expected behavior
   - Actual behavior
   - Your environment (Python version, OS, etc.)
   - If possible, a minimal code example that reproduces the issue

## Feature Requests

If you have an idea for a new feature:

1. Check if the feature has already been requested in the GitHub Issues
2. If not, create a new issue with:
   - A clear title that summarizes the feature
   - A detailed description of the feature
   - Examples of how it would be used
   - Any relevant context or use cases

## Questions and Feedback

If you have questions or feedback:

- For general questions, create a GitHub Discussion
- For specific issues, create a GitHub Issue

## License

By contributing to Recursivist, you agree that your contributions will be licensed under the project's MIT License.
